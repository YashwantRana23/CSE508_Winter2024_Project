"""Frozen local sentence encoder + offline-trained linear classification heads.

Labels describe a question, never the truth, applicability, or completeness of law.
Request handling performs no training, model download, or question persistence.
"""
import json
import logging
from pathlib import Path
from threading import RLock
from time import monotonic

import numpy as np
from app.config import get_settings
from app.services.retrieval_service import EmbeddingInputTooLongError, encode_texts

logger = logging.getLogger(__name__)
MODEL_PATH = Path(__file__).resolve().parents[1] / "data" / "classification" / "model.json"
COOLDOWN_SECONDS = 60
_lock = RLock()
_cached_key = None
_cached_model = None
_failure_key = None
_failed_until = 0.0
_LABELS = {
    "scope": {"historical", "current", "comparison"},
    "intent": {"section_lookup", "explanation", "comparison", "unrelated"},
}


def _unavailable() -> dict:
    return {
        "status": "unavailable", "model_version": None,
        "scope": "uncertain", "intent": "uncertain",
        "note": "Local classification is unavailable. Source selection and document retrieval remain available.",
    }


def _artifact_key(encoder: str) -> tuple:
    try:
        stat = MODEL_PATH.stat()
        return (encoder, stat.st_mtime_ns, stat.st_size)
    except OSError:
        return (encoder, None, None)


def _load_model(encoder: str) -> dict:
    # JSON numeric arrays avoid executable pickle/joblib model artifacts.
    if MODEL_PATH.stat().st_size > 2_000_000:
        raise ValueError("Classifier artifact is too large.")
    artifact = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    if artifact.get("format_version") != 1 or artifact.get("encoder_model") != encoder:
        raise ValueError("Classifier encoder or format does not match.")
    if artifact.get("normalized_embeddings") is not True:
        raise ValueError("Classifier requires normalized embeddings.")
    version = artifact.get("model_version")
    dimension = artifact.get("embedding_dimension")
    if not isinstance(version, str) or not version or len(version) > 100:
        raise ValueError("Invalid model version.")
    if type(dimension) is not int or not 1 <= dimension <= 4096:
        raise ValueError("Invalid embedding dimension.")
    parsed = {"model_version": version, "embedding_dimension": dimension, "heads": {}}
    for name, supported in _LABELS.items():
        head = artifact["heads"][name]
        classes = head["classes"]
        if not isinstance(classes, list) or len(classes) != len(supported) or set(classes) != supported:
            raise ValueError("Unsupported classifier labels.")
        coefficients = np.asarray(head["coefficients"], dtype=np.float64)
        intercept = np.asarray(head["intercept"], dtype=np.float64)
        threshold = np.asarray([head["min_score"], head["min_margin"]], dtype=np.float64)
        if coefficients.shape != (len(classes), dimension) or intercept.shape != (len(classes),):
            raise ValueError("Invalid classifier dimensions.")
        if threshold.shape != (2,) or not all(np.isfinite(array).all() for array in (coefficients, intercept, threshold)):
            raise ValueError("Non-finite classifier values.")
        if not np.all((threshold >= 0) & (threshold <= 1)):
            raise ValueError("Invalid classifier thresholds.")
        parsed["heads"][name] = {"classes": classes, "coef": coefficients, "intercept": intercept, "threshold": threshold}
    return parsed


def _predict(vector: np.ndarray, head: dict) -> str:
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        logits = head["coef"] @ vector + head["intercept"]
        if not np.isfinite(logits).all():
            raise ValueError("Invalid classifier logits.")
        weights = np.exp(logits - np.max(logits))
        scores = weights / weights.sum()
        if not np.isfinite(scores).all():
            raise ValueError("Invalid classifier scores.")
    order = np.argsort(-scores, kind="stable")
    top, second = order[:2]
    if scores[top] < head["threshold"][0] or scores[top] - scores[second] < head["threshold"][1]:
        return "uncertain"
    return head["classes"][int(top)]


def classify(question: str) -> dict:
    global _cached_key, _cached_model, _failure_key, _failed_until
    encoder = get_settings().EMBEDDING_MODEL
    key = _artifact_key(encoder)
    with _lock:
        if key == _failure_key and monotonic() < _failed_until:
            return _unavailable()
        try:
            if key != _cached_key or _cached_model is None:
                _cached_model = _load_model(encoder)
                _cached_key = key
            artifact = _cached_model
            # No text or embedding is saved; the shared encoder caches only its weights.
            try:
                vector = np.asarray(encode_texts([question], reject_truncation=True), dtype=np.float64)
            except EmbeddingInputTooLongError:
                return {
                    "status": "ready", "model_version": artifact["model_version"],
                    "scope": "uncertain", "intent": "uncertain",
                    "note": "This question exceeds the local classifier's token limit. Shorten it to receive advisory labels; document retrieval remains available.",
                }
            if vector.shape != (1, artifact["embedding_dimension"]) or not np.isfinite(vector).all():
                raise ValueError("Encoder output does not match classifier.")
            scope = _predict(vector[0], artifact["heads"]["scope"])
            intent = _predict(vector[0], artifact["heads"]["intent"])
            if intent == "unrelated":
                scope = "uncertain"
            _failure_key = None
            _failed_until = 0.0
            note = "Local model suggestion, not a legal finding or a calibrated probability."
            if "uncertain" in (scope, intent):
                note += " At least one label is uncertain; keep the selected source or clarify the question."
            return {"status": "ready", "model_version": artifact["model_version"], "scope": scope, "intent": intent, "note": note}
        except Exception:
            _failure_key = key
            _failed_until = monotonic() + COOLDOWN_SECONDS
            logger.warning("Local question classifier unavailable; retrying after cooldown.")
            return _unavailable()
