# Legal Lens 2.0 release scope

This release targets a practical local demo with reviewable feature PRs. The larger upgrade roadmap remains a proposal; this document identifies the smaller implementation scope selected for the same-day build.

## Feature stack

Each PR builds on the previous branch so review diffs stay focused. Merge in order only after review, then update downstream PR bases as needed. Publishing a PR does not imply approval, a passed remote check, or a merge.

| Order | Branch / PR | Review scope |
| --- | --- | --- |
| 1 | `legal-lens/local-demo-foundation` · [PR #3](https://github.com/YashwantRana23/CSE508_Winter2024_Project/pull/3) | Working direct-access app, local setup/configuration, dependency baseline, prior demo repairs. |
| 2 | `legal-lens/shared-retrieval` · [PR #4](https://github.com/YashwantRana23/CSE508_Winter2024_Project/pull/4) | Registered PDF sources, BM25/MiniLM retrieval with RRF, actual-method metadata, page/version links. |
| 3 | `legal-lens/grounded-assistant` · [PR #5](https://github.com/YashwantRana23/CSE508_Winter2024_Project/pull/5) | Shared evidence in chat, bounded citation references, keyless excerpts, provider cooldown/retry, explicit response modes. |
| 4 | `legal-lens/research-workspace` · [PR #6](https://github.com/YashwantRana23/CSE508_Winter2024_Project/pull/6) | Source-aware UI, retrieval/mode controls, source inspection, Markdown brief export. |
| 5 | `legal-lens/release-packaging` · final release branch | Documentation, CPU Docker Compose packaging, and build-only GitHub checks. |

The feature contracts live in the Pydantic schemas and OpenAPI `/docs`. PR descriptions should record the checks actually executed on the corresponding branch. Container build/run and successful paid generation must stay listed as unverified if the environment did not permit them.

## Included implementation scope

- Shared PDF-based retrieval for search and chat, with page-aware excerpts and registered source links.
- BM25 lexical baseline; optional locally cached MiniLM semantic path and RRF fusion.
- A keyless excerpt experience, explicit provider failures, and a bounded provider retry cooldown.
- Source-backed research UI and Markdown brief export.
- Persistent local feedback/cache storage, reproducible setup instructions, and build-only CI.

## Deferred from the larger roadmap

| Deferred feature | Reason / prerequisite |
| --- | --- |
| Verified current-law BNS/BNSS/BSA corpus and IPC mapping | Requires authoritative sources, legal version/provision validation, permissions, and review. Historical book remains clearly labeled. |
| Cross-encoder reranking and labeled retrieval benchmark | Needs representative questions, expected evidence, and measured quality/latency tradeoffs. |
| OCR and multilingual research | Needs suitable documents, language-specific evaluation, and extraction-quality checks. |
| Legal entity/relation knowledge graph | Existing graph is document similarity; structured legal relations need a separate extraction and validation design. |
| Uploads, accounts, private workspaces, multi-tenant storage | Needs ownership/access controls, file processing limits, persistence, and privacy design. |
| Agents, MCP integrations, vector database migration | Add only after a concrete workflow/scale need; current local corpus does not require all of them. |
| Public production deployment | Needs HTTPS, host-specific origins, abuse/rate/cost controls, operational monitoring, and verified container/runtime behavior. |

## Acceptance boundaries

A successful local release shows a retrieved passage, opens the correct PDF page, labels the real answer/retrieval mode, and exports a brief with traceable sources. Build and dependency checks establish technical consistency, not current-law correctness. Executed checks and remaining verification are recorded in [VERIFICATION.md](VERIFICATION.md). The [manual demo checklist](DEMO.md) supports repeatable presentation; PR validation notes identify the branch checked.

Do not claim a completed current-law update, state-of-the-art accuracy, universal company readiness, production security, or sole authorship. Resume strength comes from a working demo, clear design choices, and contributions that reviewers can inspect.
