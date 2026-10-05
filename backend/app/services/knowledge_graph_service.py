"""
Knowledge graph from top-N documents: cosine similarity matrix, graph structure,
and reranked top 3 by average similarity.
"""
import re
from typing import List, Dict, Any

import networkx as nx
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _doc_to_short_text(text: str, max_words: int = 50) -> str:
    words = re.findall(r"\b\w+\b", (text or "")[:5000])
    return " ".join(words[:max_words])


def calculate_similarity_matrix(documents: List[str]) -> np.ndarray:
    n = len(documents)
    docs = [d.strip() or " " for d in documents]
    vectorizer = TfidfVectorizer(min_df=1, token_pattern=r"(?u)\b\w+\b")
    try:
        tfidf = vectorizer.fit_transform(docs)
        if tfidf.shape[1] == 0:
            raise ValueError("empty vocabulary")
    except ValueError:
        # Fallback when vocabulary is empty (e.g. only stop words)
        return np.eye(n)
    return cosine_similarity(tfidf, tfidf)


def build_knowledge_graph(
    documents: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    documents: [{"text": "...", "name": "..."}, ...] (e.g. BM25 top 10)
    Returns: {nodes, edges, top_3} for frontend visualization and display.
    """
    if not documents:
        return {"nodes": [], "edges": [], "top_3": []}

    texts = [_doc_to_short_text(d.get("text", "")) for d in documents]
    names = [str(d.get("name", f"doc_{i}")) for i, d in enumerate(documents)]

    node_ids = [f"doc_{i}" for i in range(len(documents))]

    sim_matrix = calculate_similarity_matrix(texts)
    avg_similarities = np.mean(sim_matrix, axis=1)
    ranked_indices = np.argsort(-avg_similarities, kind="stable")

    G = nx.DiGraph()
    for i, idx in enumerate(ranked_indices):
        name = names[idx]
        G.add_node(
            node_ids[idx],
            label=texts[idx][:200],
            avg_similarity=float(avg_similarities[idx]),
            rank=i + 1,
        )

    for i in range(len(documents)):
        for j in range(len(documents)):
            if i != j:
                G.add_edge(node_ids[i], node_ids[j], weight=float(sim_matrix[i][j]))

    nodes = [
        {
            "id": n,
            "label": G.nodes[n].get("label", n),
            "rank": G.nodes[n]["rank"],
            "avg_similarity": G.nodes[n]["avg_similarity"],
        }
        for n in G.nodes()
    ]
    edges = [
        {"source": u, "target": v, "weight": G.edges[u, v]["weight"]}
        for u, v in G.edges()
    ]

    top_3 = []
    for i, idx in enumerate(ranked_indices[:3]):
        top_3.append({
            "rank": i + 1,
            "text": documents[idx].get("text", ""),
            "name": names[idx],
        })

    return {"nodes": nodes, "edges": edges, "top_3": top_3}


def rerank_top_3(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Same logic as build_knowledge_graph but returns only top 3 reranked."""
    result = build_knowledge_graph(documents)
    return result["top_3"]
