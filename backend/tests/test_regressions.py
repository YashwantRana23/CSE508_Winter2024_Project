import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_temp = tempfile.TemporaryDirectory()
os.environ["DATABASE_URL"] = "sqlite:///" + str(Path(_temp.name) / "test.db")

from fastapi.testclient import TestClient
from app.main import app
from app import config
from app.services import bm25_service, chatbot_service, knowledge_graph_service


class RegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        from app.database import engine
        engine.dispose()
        _temp.cleanup()

    def setUp(self):
        bm25_service._corpus_df = None
        bm25_service._tokens_list = None
        bm25_service._bm25_index = None

    def test_dotenv_loaded_before_database_and_secret_settings(self):
        def fake_load():
            os.environ["SECRET_KEY"] = "test-secret"
            os.environ["DATABASE_URL"] = "sqlite:///from-dotenv.db"
        with patch.dict(os.environ), patch.object(config, "_load_dotenv", side_effect=fake_load):
            settings = config.get_settings()
            self.assertEqual(settings.SECRET_KEY, "test-secret")
            self.assertEqual(settings.DATABASE_URL, "sqlite:///from-dotenv.db")

    def test_demo_search_and_no_matches(self):
        with patch.object(bm25_service._settings, "DATA_PATH", None):
            response = self.client.post("/search/bm25", json={"query": "maternity benefit"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["results"][0]["name"], "maternity.txt")
            self.assertEqual(self.client.post("/search/bm25", json={"query": "zzzzzzzzz"}).json()["results"], [])

    def test_invalid_search_inputs(self):
        for payload in ({"query": " "}, {"query": "law", "top_k": 0}, {"query": "law", "top_k": -1}, {"query": "law", "top_k": 51}):
            self.assertEqual(self.client.post("/search/bm25", json=payload).status_code, 422)

    def test_invalid_corpus_returns_actionable_error(self):
        cases = ["wrong,name\nvalue,file\n", "text,name\n", "text,name\n!!!,file\n"]
        for content in cases:
            self.setUp()
            path = Path(_temp.name) / "corpus.csv"
            path.write_text(content)
            with patch.object(bm25_service._settings, "DATA_PATH", str(path)):
                response = self.client.post("/search/bm25", json={"query": "law"})
                self.assertEqual(response.status_code, 503)
        self.setUp()
        with patch.object(bm25_service._settings, "DATA_PATH", str(Path(_temp.name)/"missing.csv")):
            self.assertEqual(self.client.post("/search/bm25", json={"query": "law"}).status_code, 503)

    def test_duplicate_document_names_keep_separate_nodes(self):
        docs = [{"name": "same", "text": "maternity benefit law"}, {"name": "same", "text": "child labour law"}]
        response = self.client.post("/knowledge-graph/generate", json={"documents": docs})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len({node["id"] for node in data["nodes"]}), 2)
        self.assertTrue(all(edge["source"] != edge["target"] for edge in data["edges"]))
        self.assertEqual(len(data["top_3"]), 2)
        self.assertEqual(self.client.post("/rerank/cosine", json={"documents": docs}).status_code, 200)

    def test_graph_empty_and_malformed_documents(self):
        self.assertEqual(self.client.post("/knowledge-graph/generate", json={"documents": []}).json()["nodes"], [])
        for doc in ({"text": None, "name": "x"}, {"text": 123, "name": "x"}, {"text": " ", "name": "x"}):
            self.assertEqual(self.client.post("/knowledge-graph/generate", json={"documents": [doc]}).status_code, 422)

    def test_feedback_persistence_and_validation(self):
        response = self.client.post("/feedback/submit", json={"message": "Test feedback"})
        self.assertEqual(response.status_code, 200)
        from app.database import SessionLocal
        from app.models.feedback import Feedback
        with SessionLocal() as db:
            self.assertEqual(db.get(Feedback, response.json()["id"]).message, "Test feedback")
        for body in ({"message": " "}, {"message": "test", "email": "invalid"}):
            self.assertEqual(self.client.post("/feedback/submit", json=body).status_code, 422)

    def test_chat_status_no_key_and_missing_domain_pdf(self):
        with patch.object(chatbot_service.settings, "OPENAI_API_KEY", None):
            data = self.client.get("/chatbot/status").json()
            self.assertFalse(data["ipc"]["available"])
            self.assertIn("OPENAI_API_KEY", data["ipc"]["reason"])
            self.assertEqual(self.client.post("/chatbot/ipc", json={"message": "Hello"}).status_code, 503)
        with patch.object(chatbot_service.settings, "CHATBOT_MURDER_PDF", "does-not-exist.pdf"):
            self.assertIsNone(chatbot_service._resolve_pdf_path("murder"))

    def test_chat_history_is_request_scoped(self):
        chain = MagicMock()
        chain.invoke.return_value = {"answer": "An answer"}
        with patch.object(chatbot_service, "_get_chain_for_domain", return_value=chain):
            chatbot_service.chat("ipc", "Follow up", [{"role": "user", "content": "My question"}, {"role": "assistant", "content": "My answer"}])
            first = chain.invoke.call_args.args[0]
            self.assertEqual([m.content for m in first["chat_history"]], ["My question", "My answer"])
            chatbot_service.chat("ipc", "A new visitor")
            self.assertEqual(chain.invoke.call_args.args[0]["chat_history"], [])

    def test_embedding_cache_reuse_and_invalidation(self):
        from langchain_core.embeddings import Embeddings
        class TestEmbeddings(Embeddings):
            calls = 0
            def embed_documents(self, texts):
                self.calls += 1
                return [[1.0, 0.0] for _ in texts]
            def embed_query(self, text):
                return [1.0, 0.0]
        embeddings = TestEmbeddings()
        pdf = Path(_temp.name) / "fake.pdf"
        pdf.write_bytes(b"version-one")
        with patch.object(chatbot_service, "BASE_DIR", Path(_temp.name)), \
             patch.object(chatbot_service, "domain_status", return_value={"available": True}), \
             patch.object(chatbot_service, "_resolve_pdf_path", return_value=pdf), \
             patch.object(chatbot_service, "_get_pdf_text", return_value="maternity benefit law"), \
             patch.object(chatbot_service.settings, "EMBEDDING_MODEL", "test-model"), \
             patch.dict(chatbot_service._chains, {}, clear=True), \
             patch("langchain_community.embeddings.HuggingFaceEmbeddings", return_value=embeddings), \
             patch("langchain_openai.ChatOpenAI"), \
             patch("langchain.chains.ConversationalRetrievalChain.from_llm", return_value=MagicMock()):
            chatbot_service._get_chain_for_domain("ipc")
            chatbot_service._chains.clear()
            chatbot_service._get_chain_for_domain("ipc")
            self.assertEqual(embeddings.calls, 1)
            pdf.write_bytes(b"version-two")
            chatbot_service._chains.clear()
            chatbot_service._get_chain_for_domain("ipc")
            self.assertEqual(embeddings.calls, 2)
            for cache in (Path(_temp.name)/"instance"/"embeddings").glob("*.npz"):
                cache.write_bytes(b"corrupt cache")
            chatbot_service._chains.clear()
            chatbot_service._get_chain_for_domain("ipc")
            self.assertEqual(embeddings.calls, 3)

    def test_chat_validation_and_removed_auth_routes(self):
        for path, body in [("/chatbot/unknown", {"message": "Hello"}), ("/chatbot/ipc", {"message": " "}), ("/chatbot/ipc", {"message": "Hi", "history": [{"role": "system", "content": "bad"}]}), ("/chatbot/ipc", {"message": "Hi", "domain": "child"})]:
            self.assertEqual(self.client.post(path, json=body).status_code, 422)
        self.assertEqual(self.client.post("/auth/register", json={}).status_code, 404)

if __name__ == "__main__":
    unittest.main()
