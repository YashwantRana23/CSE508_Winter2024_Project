# Five-minute Legal Lens 2.0 demo

## Before presenting

Start the local app and open the dashboard. Keep the backend terminal/logs available for troubleshooting. Warm one retrieval request before timing a demo: PDF extraction and embedding construction have a different cost from cached retrieval. For a predictable keyless demo, select document-excerpt mode. Download the MiniLM model beforehand only if demonstrating hybrid retrieval.

Use the bundled IPC corpus and describe it as **historical research material**. A generated answer requires a configured provider, model access, and credits; an excerpt response is a valid separate feature, not evidence that generation succeeded.

## Presentation sequence

| Time | Action | What it demonstrates |
| --- | --- | --- |
| 0:00–0:40 | Open the dashboard and identify the active corpus/status. | Direct access, explicit historical scope, and visible source availability. |
| 0:40–1:40 | Search “What does Section 302 say about punishment for murder?” with the selected retrieval method. | Real PDF retrieval, actual method reporting, ranked excerpts, and page metadata. |
| 1:40–2:40 | Open a retrieved source. Compare its excerpt with the original PDF page. | Inspectable evidence and a source-version-aware page link. A page number is not an accuracy score. |
| 2:40–3:30 | Ask the same question in document-excerpt mode. If a funded provider is available, separately show auto mode and its returned mode. | Shared retrieval across search/chat and keyless behavior. State whether this answer was generated or extracted. |
| 3:30–4:20 | Export a Markdown research brief and open it. | A portable record of the research context, sources, and corpus limitation. |
| 4:20–5:00 | Show the architecture and feature PRs. Explain one limitation and one next step. | Engineering decisions, reviewable delivery, and an honest scope. |

If hybrid search reports BM25 fallback, explain the missing/failed local model using the displayed warning. Do not call a lexical-only response hybrid. If a configured domain has no PDF, show its unavailable state rather than selecting another source silently.

## Optional classifier demonstration

In the assistant, ask “Today I am studying the old IPC. Explain Section 302.” Open **Question understanding** to inspect the local scope/intent estimate. Then ask “How does IPC Section 302 compare with BNS?” and show the source-scope refusal with retrieval marked skipped. Try an unclear question to show `uncertain`. The labels use the cached MiniLM encoder and local logistic-regression heads, without API credits. Export a brief to retain the classification note alongside the evidence.

The classifier's small authored evaluation is distinct from retrieval or legal-answer accuracy. See [classifier details](CLASSIFICATION.md) before citing any metric.

## Lightweight evidence to record

This is a manual demo checklist, not a regression suite. Fill it using actual observations; a blank row means unverified.

| Observation | Result / evidence |
| --- | --- |
| Git commit and date used for the demo | |
| Dashboard and `/health` load | |
| Search method requested / actual method returned | |
| Source title, document ID, PDF page, and version link | |
| PDF page agrees with the displayed excerpt | |
| Assistant returned mode and visible reason | |
| Keyless excerpts work with no provider call | |
| Markdown export opens and retains sources/scope | |
| Frontend build/lint/types and Python dependency/syntax checks | |
| Container build/run, only if performed | |

Record first-request and warm-request timings separately if you report latency. Do not infer retrieval quality from one successful question. RRF similarity/rank values are not calibrated confidence scores. No accuracy, recall, or latency benchmark is claimed until a fixed question set, expected evidence, machine details, and actual outputs are recorded.

## Resume and interview wording

A defensible summary after the feature code is integrated and demonstrated:

> Extended a collaborative legal-research prototype with shared BM25/semantic retrieval, page-level source inspection, provider-independent excerpt mode, and Markdown research-brief export using FastAPI and Next.js.

If demonstrating lexical fallback only, say **BM25 retrieval with an optional semantic path** rather than implying hybrid results were measured. Mention container packaging only as packaging until its build/run is verified. Keep the original group attribution and explain your own contributions through the feature PRs.

Prepare to explain why search and chat share retrieval, how source identifiers are validated, why the corpus remains historical, what happens when credits run out, and which pieces were deliberately deferred. The document-similarity graph remains a TF-IDF feature; it is not a legal knowledge graph.
