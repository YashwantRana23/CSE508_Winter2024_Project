# Local question classifier model card

Version: `minilm-question-router-v1`. This is an original local baseline inspired by small task-specific classifiers. It is not Jev, a reproduction of Jev, a generative model, or a legal-validity classifier.

## Purpose and outputs

The frozen `sentence-transformers/all-MiniLM-L6-v2` CPU encoder produces normalized 384-dimensional embeddings. Two separately trained scikit-learn logistic-regression heads suggest labels:

| Head | Labels | Meaning |
| --- | --- | --- |
| Scope | `historical`, `current`, `comparison` | Historical-source question, operative/current-law question, or a comparison across old and current regimes. |
| Intent | `section_lookup`, `explanation`, `comparison`, `unrelated` | Requested task, independently of the time scope. |

Each head may abstain with `uncertain`. Comparing two historical IPC provisions has **historical scope and comparison intent**; scope `comparison` is reserved for comparisons across legal regimes. Questions unrelated to legal research have no scope annotation; a confidently predicted `unrelated` intent forces the returned scope to `uncertain`.

The labels are advisory. Source metadata and explicit application rules remain authoritative. The model cannot determine legal applicability, whether evidence is sufficient, whether a source is current, or whether a generated answer is true. It must not silently select an unavailable corpus or authorize a current-law answer from historical material. The chat integration keeps requests in excerpt mode when either scope or intent is uncertain, or when the classifier is unavailable.

## Dataset provenance and separation

`train.json` contains 164 original questions, `validation.json` 56, and `test.json` 56. All were authored and reviewed by coding agents for this prototype, **not annotated or validated by human legal experts**, and were not collected from real users. They are English illustrative questions. This is not an external or statistically representative benchmark.

The scope head trains on 140 questions and evaluates on 48 per evaluation split, excluding unrelated questions. The intent head uses all questions. Exact normalized duplicates are rejected within and across splits. Normalization applies Unicode NFKC, case folding, and punctuation/whitespace folding. Split examples were authored separately, but related task families and writing style recur across splits; semantic similarity remains a limitation.

The annotation convention treats an unambiguous present/applicable-law request as `current`, even where it supplies a date instead of the word "current". Incidental study dates do not change an otherwise explicit historical IPC question. The dataset includes these counterexamples and distinctions between within-era and cross-era comparisons.

## Training and threshold selection

Training uses the fixed frozen encoder plus logistic regression with `C=12`, `max_iter=2000`, and `random_state=508`. No legal-answer generation, provider API key, or API calls are used. The encoder must already be cached locally. No network download or fitting occurs during web requests.

The validation split alone selects a minimum top-class score and minimum top-two margin for each head. The grid chooses maximum coverage with validation accepted accuracy at least 95%, breaking coverage ties toward larger margins, then scores. If no candidate qualifies, all requests abstain. This 95% threshold-selection target is **not a performance guarantee**. Model scores are uncalibrated; neither scores nor accuracy represent legal correctness.

Selected thresholds: scope top score 0.65 / margin 0.30; intent top score 0.65 / margin 0.40. The test split was evaluated after weights and thresholds were fixed. There was no tuning or data revision in response to its results.

## Observed illustrative held-out results

| Head | Raw accuracy, before abstention | Raw macro F1 | Accepted accuracy | Coverage |
| --- | --- | --- | --- | --- |
| Scope | 42/48 = 87.50% | 0.7857 | 39/42 = 92.86% | 42/48 = 87.50% |
| Intent | 53/56 = 94.64% | 0.9440 | 44/46 = 95.65% | 46/56 = 82.14% |

Coverage means the fraction receiving a label instead of `uncertain`. Accepted accuracy excludes abstained examples, so it must always be reported together with coverage and the sample count. The validation accepted accuracy was 40/42 (95.24%) for scope and 46/48 (95.83%) for intent.

**Known weakness:** raw scope recall for cross-era comparisons is only 3/8 in the held-out set; two were confused with current questions and three with historical questions. Current labels still trigger the application's source boundary, while historical misclassification is the more concerning direction and requires independent source/current-law rules. The scope classifier is unsuitable as the sole current-law safeguard. A confidently wrong classification remains possible. Long, multilingual, mixed-intent, unusual, or adversarial questions and real legal-user language are not validated by this dataset. High handcrafted-example performance should not be described as production accuracy.

`evaluation.json` stores counts, confusion matrices, example IDs for errors/abstentions, threshold protocol, fixed configuration, software versions, and dataset SHA-256 hashes. Dataset JSON uses LF line endings via `.gitattributes` so hashes survive Windows/Linux checkout differences. The report evaluates the two heads, not the complete chat/source-policy pipeline.

## Runtime behavior and failure handling

`POST /questions/classify` accepts a trimmed question of 1–4000 characters. Responses contain only `status`, `model_version`, `scope`, `intent`, and `note`; they do not expose a percentage presented as certainty. `classification_service.classify(question)` provides the same result to the application.

The shared CPU encoder is reused. No question text or embeddings are persisted or retained in a classification cache. The classifier checks the tokenizer's actual token count including special tokens; a question exceeding the encoder's limit receives two `uncertain` labels without embedding a silently truncated question. This does not disable the classifier for subsequent requests.

The runtime reads numeric weights from `model.json`, not executable pickle/joblib files. It validates the format, model ID, dimensions, classes, thresholds, and finite numbers. A missing/invalid artifact, missing cached encoder, or embedding-model mismatch returns `unavailable` with uncertain labels. A 60-second cooldown prevents repeated failed loads; changing artifact metadata or the configured encoder allows another attempt immediately. Existing retrieval remains available through its separate fallback.

The artifact pins the encoder **model ID**, not an immutable upstream revision. Reproduce with the same cached encoder weights and recorded software versions; if the encoder changes, retrain and evaluate before using these coefficients. A matching model ID alone cannot detect a modified local cache.

## Reproduce offline training

From `backend`, with the configured MiniLM weights already cached:

```powershell
.\.venv\Scripts\python.exe scripts\train_question_classifier.py
```

This intentionally writes `model.json` and `evaluation.json`. Use `--output-dir <directory>` to preserve the checked-in artifact. The script rejects unsupported labels, missing training classes, invalid questions, and normalized duplicate questions before fitting. It never modifies labels automatically. Future model improvements should freeze a new untouched test split rather than repeatedly optimizing against this exposed one.

For a resume, describe a **local classifier with uncertainty handling** and give these small illustrative benchmark counts explicitly. Do not claim a legally validated model, Jev equivalence, or general-purpose legal reasoning.
