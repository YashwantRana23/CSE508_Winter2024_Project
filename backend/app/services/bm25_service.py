"""
BM25 search service. Uses corpus from CSV (DATA_PATH) or in-memory fallback.
Returns top K results (default 10) per query.
"""
import re
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi

from app.config import get_settings, PROJECT_ROOT

# Gensim-style preprocessing (lowercase, tokenize, remove stopwords-like)
try:
    from gensim.parsing.preprocessing import preprocess_string
except ImportError:
    # Fallback: simple tokenization
    def preprocess_string(s: str):
        s = (s or "").lower()
        tokens = re.findall(r"\w+", s)
        return tokens


_settings = get_settings()
_corpus_df: pd.DataFrame | None = None
_tokens_list: List[List[str]] | None = None
_bm25_index: BM25Okapi | None = None


def _resolve_data_path() -> Path | None:
    path = _settings.DATA_PATH
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p if p.exists() else None


def _load_corpus() -> Tuple[pd.DataFrame, List[List[str]]]:
    """Load corpus CSV (columns: text, name) and tokenized list."""
    global _corpus_df, _tokens_list
    if _corpus_df is not None:
        return _corpus_df, _tokens_list

    path = _resolve_data_path()
    if path:
        df = pd.read_csv(path)
        if "text" not in df.columns:
            df = df.rename(columns={df.columns[0]: "text"})
        if "name" not in df.columns and len(df.columns) >= 2:
            df["name"] = df.iloc[:, 1].astype(str)
        elif "name" not in df.columns:
            df["name"] = [f"doc_{i}" for i in range(len(df))]
        df["text"] = df["text"].fillna("").astype(str)
    else:
        # Minimal in-memory corpus so app runs without DATA_PATH
        df = pd.DataFrame({
            "text": [
                "Indian Penal Code Section 302 deals with punishment for murder.",
                "Child labour is prohibited under various Indian laws.",
                "Maternity benefit is provided under the Maternity Benefit Act.",
            ],
            "name": ["ipc_302.txt", "child_law.txt", "maternity.txt"],
        })

    _corpus_df = df
    _tokens_list = [preprocess_string(t) for t in df["text"].tolist()]
    return _corpus_df, _tokens_list


def get_bm25_index() -> BM25Okapi:
    """Lazy-load and return BM25 index."""
    global _bm25_index
    if _bm25_index is not None:
        return _bm25_index
    _, tokens = _load_corpus()
    _bm25_index = BM25Okapi(tokens)
    return _bm25_index


def search(query: str, top_k: int | None = None) -> List[Tuple[int, float]]:
    """
    Return list of (index, score) for top_k results.
    """
    top_k = top_k or _settings.BM25_TOP_K
    bm25 = get_bm25_index()
    df, _ = _load_corpus()
    search_tokens = preprocess_string(query)
    scores = bm25.get_scores(search_tokens)
    top_indexes = np.argsort(scores)[::-1][:top_k]
    return [(int(i), float(scores[i])) for i in top_indexes if scores[i] > 0]


def get_bm25_results(query: str, top_k: int | None = None) -> List[dict]:
    """Return list of {text, name, score, rank} for API."""
    df, _ = _load_corpus()
    hits = search(query, top_k)
    return [
        {
            "text": df.iloc[idx]["text"],
            "name": str(df.iloc[idx].get("name", f"doc_{idx}")),
            "score": score,
            "rank": r + 1,
        }
        for r, (idx, score) in enumerate(hits)
    ]
