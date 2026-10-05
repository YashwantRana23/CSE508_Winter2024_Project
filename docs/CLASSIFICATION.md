# Local question classification

Legal Lens uses its existing cached `sentence-transformers/all-MiniLM-L6-v2` encoder with two logistic-regression heads. MiniLM stays frozen. Training fits only the heads. This is neither a Jev implementation nor SetFit embedding fine-tuning; SetFit is a possible later experiment if a larger reviewed dataset warrants it.

## What the labels mean

| Head | Labels | Purpose |
| --- | --- | --- |
| Scope | historical, current, comparison, uncertain | Distinguishes research in historical material from requests requiring current or cross-era evidence. Scope comparison means comparison across historical/current regimes. |
| Intent | section_lookup, explanation, comparison, unrelated, uncertain | Describes how a question is phrased; intent alone never selects a source or denies retrieval. |

“Compare IPC sections 299 and 300 in this book” can have historical scope and comparison intent. “Compare IPC with BNS” requires cross-era sources. Unrelated questions can have uncertain scope; a question without a clear supported label should not be forced into one.

Each head has acceptance thresholds for its top class score and margin over the next class. Values are routing heuristics selected using the validation split, not calibrated probabilities of legal correctness. The UI deliberately reports labels and uncertainty rather than an accuracy percentage.

## Runtime and failure behavior

1. `POST /questions/classify` validates a bounded question and returns `status`, `model_version`, `scope`, `intent`, and `note`.
2. The assistant obtains the same classification before retrieval. Historical/unverified source metadata and independent scope rules remain authoritative.
3. Explicit BNS/BNSS/BSA references, current-law language attached to a legal request, and dated applicability requests need a verified source. Bare “today” is insufficient. These patterns do not establish a legal cutoff date or decide which statute applies. Literal patterns can conservatively reject negated phrases such as “without reference to new law”; they do not understand all negation or paraphrases.
4. When both heads accept their labels, current or cross-era scope also causes a conservative scope refusal for the existing historical/unverified source types. Retrieval is explicitly marked skipped. Misclassification can refuse a valid question; rephrase around a specific historical passage or use source search to inspect it.
   If an explicit historical-book reference conflicts with the learned estimate, and no deterministic scope rule matches, the assistant preserves retrieval and uses excerpts. It retains the raw classifier label and explains the disagreement. An old-book reference never overrides an explicit current-law/applicability rule.
5. Unavailable classification or uncertain scope/intent preserves retrieval and returns excerpts without provider generation. Intent estimates are displayed for inspection; no implicit corpus switching occurs.

The model loads from a JSON coefficient artifact, without pickle deserialization. The local encoder is shared with retrieval. There is no request-time training, embedding-model download, API call, or persistent question storage in the classifier. Failures return unavailable/uncertain and use a retry cooldown. Search remains usable with BM25 without an encoder. An administrator changing `EMBEDDING_MODEL` must train compatible heads; existing coefficients must not be used with a different encoder.

Classification adds first-use model load time even when chat retrieval is set to BM25. Warm the assistant before a demo. Retrieval milliseconds describe only retrieval, not classifier loading or end-to-end latency. A skipped retrieval has zero elapsed retrieval time and an explicit warning.

## Training and evidence

The checked-in questions are original authored, agent-reviewed development examples. They have not been reviewed by a legal expert or collected as a representative real-user dataset. Training, threshold-validation, and evaluation splits are separate. The evaluation split is not used to fit the heads or select thresholds. Questions and labels are reviewable in the dataset files; normalized duplicate questions across splits are rejected by the training script.

See the [dataset/model card](../backend/app/data/classification/README.md) for the exact split sizes, reproducible training command, artifact metadata, chosen thresholds, and measured results. The committed report is scoped to this small authored dataset. Do not translate it into a general legal accuracy claim, a production readiness claim, or a Jev comparison.

No historical regression suite is required for this feature. Focused verification covers the classifier output, uncertainty/missing-model behavior, source-scope policy, chat excerpts, and UI display/export. Existing build-only CI performs no model download or model training.

## Demo questions

- “Today I am studying the old IPC. Explain Section 302.” — incidental time wording should still permit historical retrieval.
- “Compare Section 299 and Section 300 of the historical IPC.” — historical scope with comparison intent.
- “How does IPC Section 302 compare with BNS?” — needs sources beyond the historical book; chat retrieval is skipped.
- “Which provision applies to an offence committed in 2026?” — cannot verify dated applicability from current source metadata.
- “asdasda” — uncertainty should be visible rather than a forced legal classification.

A defensible resume description is: “Added local query scope and intent classification using frozen MiniLM embeddings and logistic regression, with abstention, source-scope checks, and API-independent excerpt fallback.” Describe the evaluation dataset and limitations if quoting a metric.

## Focused verification — 5 October 2026

- Frontend ESLint, TypeScript and production build passed; Python compilation, dependency check and OpenAPI import passed.
- Live API classified the within-IPC comparison as historical/comparison, the IPC-to-BNS question as comparison/comparison, and the dated-applicability question as current/explanation.
- The incidental-today historical question returned historical/uncertain and six PDF passages. Auto mode used excerpts because intent was uncertain. Unclear text with an uncertain intent proceeded to retrieval and returned no matching evidence rather than a learned scope refusal.
- Over-limit input returned two uncertain labels; the next short request still classified normally. Empty input returned HTTP 422.
- Isolated process checks covered missing artifact, invalid JSON, encoder mismatch, and a simulated missing encoder with one load attempt across two calls during cooldown. No live settings or model files were changed by those checks.
- Browser verification showed the cross-era classification, source-scope refusal and explicit skipped-retrieval label. The downloaded Markdown brief retained the question, model version, labels, note and skipped-retrieval status. One transient browser request after backend restart succeeded through the existing Retry control.
- No regression suite was run. No provider generation call was needed for these checks. The evaluation report measures the two classifier heads on authored examples; these focused demo checks are not a legal accuracy benchmark.
