"""Offline reproducible training; no request-time fitting or provider calls.

Run from backend: python scripts/train_question_classifier.py
Weights are JSON; validation chooses abstention thresholds before test evaluation.
"""
import argparse
from collections import Counter
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import sys
import unicodedata

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.config import get_settings
from app.services.retrieval_service import encode_texts

LABELS = {
    "scope": {"historical", "current", "comparison"},
    "intent": {"section_lookup", "explanation", "comparison", "unrelated"},
}
MODEL_VERSION = "minilm-question-router-v1"


def software_versions():
    return {name: version(name) for name in ("scikit-learn", "numpy", "sentence-transformers", "torch", "transformers")}


def normalized(question):
    return re.sub(r"[^\w]+", " ", unicodedata.normalize("NFKC", question).casefold()).strip()


def load_data(directory):
    datasets, seen = {}, {}
    for split in ("train", "validation", "test"):
        records = json.loads((directory / f"{split}.json").read_text(encoding="utf-8"))
        if not isinstance(records, list) or not records:
            raise ValueError(f"Empty or invalid {split} dataset.")
        ids = set()
        for row in records:
            if not isinstance(row.get("question"), str) or not 1 <= len(row["question"].strip()) <= 4000:
                raise ValueError("Invalid question.")
            if row.get("id") in ids or not row.get("id"):
                raise ValueError("Missing/duplicate dataset ID.")
            ids.add(row["id"])
            key = normalized(row["question"])
            if not key or key in seen:
                raise ValueError(f"Normalized duplicate question in {split}; previous: {seen.get(key)}")
            seen[key] = split
            if row.get("intent") not in LABELS["intent"]:
                raise ValueError("Unsupported intent label.")
            if row.get("scope") not in LABELS["scope"] and not (row.get("scope") is None and row["intent"] == "unrelated"):
                raise ValueError("Unsupported scope label.")
            if row["intent"] == "unrelated" and row["scope"] is not None:
                raise ValueError("Unrelated questions must omit scope annotation.")
            if row["scope"] == "comparison" and row["intent"] != "comparison":
                raise ValueError("Cross-era comparison requires comparison intent.")
        datasets[split] = records
    return datasets


def selected(scores, min_score, min_margin):
    ordered = np.sort(scores, axis=1)
    return (ordered[:, -1] >= min_score) & ((ordered[:, -1] - ordered[:, -2]) >= min_margin)


def tune_thresholds(scores, labels, classes):
    predictions = classes[np.argmax(scores, axis=1)]
    candidates = []
    for score in (0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95):
        for margin in (0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5):
            mask = selected(scores, score, margin)
            count = int(mask.sum())
            if count and float(np.mean(predictions[mask] == labels[mask])) >= 0.95:
                # Max coverage, then stronger margin/score for equally sized coverage.
                candidates.append((count, margin, score))
    if not candidates:
        return 1.0, 1.0
    _, margin, score = max(candidates)
    return score, margin


def metrics(scores, labels, classes, min_score, min_margin, ids):
    prediction = classes[np.argmax(scores, axis=1)]
    accepted = selected(scores, min_score, min_margin)
    count = int(accepted.sum())
    return {
        "count": len(labels),
        "accuracy_without_abstention": round(float(accuracy_score(labels, prediction)), 4),
        "macro_f1_without_abstention": round(float(f1_score(labels, prediction, labels=classes, average="macro", zero_division=0)), 4),
        "accepted_count": count,
        "coverage": round(count / len(labels), 4),
        "accepted_accuracy": round(float(accuracy_score(labels[accepted], prediction[accepted])), 4) if count else None,
        "confusion_matrix_without_abstention": confusion_matrix(labels, prediction, labels=classes).tolist(),
        "class_order": classes.tolist(),
        "incorrect_ids_without_abstention": [identifier for identifier, truth, guess in zip(ids, labels, prediction) if truth != guess],
        "abstained_ids": [identifier for identifier, accept in zip(ids, accepted) if not accept],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=BACKEND / "app" / "data" / "classification")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    output = args.output_dir or args.data_dir
    datasets = load_data(args.data_dir)
    # Only the encoder's cached local weights are used, with no network download.
    vectors = {split: encode_texts([row["question"] for row in rows]) for split, rows in datasets.items()}
    dimension = vectors["train"].shape[1]
    if any(array.ndim != 2 or array.shape[1] != dimension or not np.isfinite(array).all() for array in vectors.values()):
        raise ValueError("Invalid encoder output.")
    artifact = {
        "format_version": 1, "model_version": MODEL_VERSION,
        "encoder_model": get_settings().EMBEDDING_MODEL,
        "normalized_embeddings": True, "embedding_dimension": int(dimension), "heads": {},
        "training": {"classifier": "sklearn LogisticRegression", "C": 12.0, "max_iter": 2000, "random_state": 508, "software_versions": software_versions()},
    }
    report = {
        "model_version": MODEL_VERSION,
        "software_versions": software_versions(),
        "provenance": "Original agent-authored and agent-reviewed illustrative questions. No human/expert annotation or real-user validation.",
        "limitation": "Small handcrafted English benchmark; measured performance is not legal accuracy, production reliability, or broad generalization. Related task families recur across splits.",
        "method": {"encoder_model": artifact["encoder_model"], "frozen_encoder": True, "classifier": "sklearn LogisticRegression", "C": 12.0, "max_iter": 2000, "random_state": 508,
                   "threshold_selection": "Validation only: maximum coverage with accepted accuracy >=0.95; ties prefer larger margin then larger score. Otherwise abstain on all.",
                   "scores": "Uncalibrated multinomial scores; not probabilities of legal correctness."},
        "split_counts": {split: len(rows) for split, rows in datasets.items()},
        "dataset_sha256": {split: hashlib.sha256((args.data_dir / f"{split}.json").read_bytes()).hexdigest() for split in datasets},
        "heads": {},
    }
    for name in LABELS:
        subsets = {}
        for split, rows in datasets.items():
            indices = [i for i, row in enumerate(rows) if row[name] is not None]
            subsets[split] = (vectors[split][indices], np.asarray([rows[i][name] for i in indices]), [rows[i]["id"] for i in indices])
        train_x, train_y, _ = subsets["train"]
        if set(train_y) != LABELS[name]:
            raise ValueError("Training set is missing classifier labels.")
        model = LogisticRegression(C=12.0, max_iter=2000, random_state=508)
        model.fit(train_x, train_y)
        validation_scores = model.predict_proba(subsets["validation"][0])
        min_score, min_margin = tune_thresholds(validation_scores, subsets["validation"][1], model.classes_)
        artifact["heads"][name] = {"classes": model.classes_.tolist(), "coefficients": model.coef_.tolist(), "intercept": model.intercept_.tolist(), "min_score": min_score, "min_margin": min_margin}
        report["heads"][name] = {
            "training_labels": dict(Counter(train_y)), "min_score": min_score, "min_margin": min_margin,
            "validation": metrics(validation_scores, subsets["validation"][1], model.classes_, min_score, min_margin, subsets["validation"][2]),
            # Test is evaluated only after the model and thresholds are fixed.
            "test": metrics(model.predict_proba(subsets["test"][0]), subsets["test"][1], model.classes_, min_score, min_margin, subsets["test"][2]),
        }
    output.mkdir(parents=True, exist_ok=True)
    for filename, content in (("model.json", artifact), ("evaluation.json", report)):
        (output / filename).write_text(json.dumps(content, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"splits": report["split_counts"], "heads": {name: {"threshold": [head["min_score"], head["min_margin"]], "test": head["test"]} for name, head in report["heads"].items()}}, indent=2))


if __name__ == "__main__":
    main()
