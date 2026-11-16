# Advanced World Bank RAG design

The user requested the advanced challenge, selected World Development Report 2021: Data for Better Lives, and authorized a maximum OpenAI budget of USD 5. The existing instruction to commit and push main remains applicable. Implementation choices below are the assistant's recommendations within that scope.

## Objective and source

Implement and honestly evaluate the full advanced task in ADVANCED.md. Do not promise a 90% score or change failed test questions to obtain it. Source: https://documents1.worldbank.org/curated/en/248201616598597113/pdf/World-Development-Report-2021-Data-for-Better-Lives.pdf . The checked file has 350 physical pages, 35,327,774 bytes, SHA-256 606c8452c8b23c01d81919c3974972bebeb1e60348a56ea40cc3ae841e301616. Copyright page 4 states CC BY 3.0 IGO with conditions for attribution, adaptation and third-party components. Share a verified download procedure and crop/page locators rather than assuming every third-party image is separately licensed.

## Approach

Use hybrid text retrieval plus vision evidence from retrieved page images. Extract native text from every page and retain the original page image, physical page number, printed label, coordinates and figure/table identifiers. Create searchable visual descriptions for useful figures/tables/diagrams across the document, not just benchmark pages. Descriptions are retrieval aids, never a substitute for verifying the original visual source. Index text and descriptions in an advanced namespace separate from Day 6 A/B. Use existing multilingual embeddings and pgvector plus a lexical index.

Alternatives considered: text/OCR alone has less cost but loses chart axes and diagram relationships; sending the whole 350-page PDF on every question has high cost and poor auditability. The combined approach reuses the database and sends only retrieved images to the answer model, with traceable source locators.

## Agent and evaluation

Use gpt-6-luna, confirmed to accept text/image input. The agent can search, inspect candidate pages/regions, calculate simple arithmetic deterministically and answer or abstain. Log every search, inspected page, image digest, context, citation, response usage, time and error. No gold, expected answer or category-derived gold region enters inference.

Prepare a separate benchmark before dev runs: Dev has 15 answerable cases (3 each tables, diagrams, charts, multi-hop, text) and 3 unanswerable. Test has exactly 30 cases: 6 tables, 5 diagrams, 5 charts, 4 multi-hop, 4 text, 6 unanswerable. Each case has one primary group, expected behavior, independently verifiable physical page/region/units/evidence and rationale. Multi-hop requires at least two distinct source pages. Dev/test must not paraphrase the same fact. Unanswerable cases should be close to the report's topic with absent details/conditions, checked against the full document.

Freeze benchmark hashes before experiments. Develop two documented configurations on Dev, select by strict pass rate with latency/cost tie breakers and freeze code/config/index hashes. Run the selected pipeline once on all 30 Test cases. Provider errors count as failures and remain in the denominator. Save any later diagnostic reruns separately; never silently repair test results.

Review every test result against original page images and the benchmark, including all citations and conditions. Record assistant-assisted labels as proposals until the learner confirms them. Report n/N by group and overall, errors, time, model, tokens, costs, coverage and extraction limitations. Bonus is only supportable if all conditions and at least 27/30 strict passes are met.

## Budget and reproducibility

Track the new advanced work separately from basic historical costs. Use local extraction/embedding where possible. Budget ledger reserves a conservative maximum before every OpenAI request, reconciles recorded usage after response, and retains an unknown-cost reserve on ambiguous failed requests. Do not exceed the authorized USD 5 estimate envelope. Any unverified invoice/tier charges are disclosed, not called exact account spend.

Cache source-derived extraction/visual descriptions by PDF/page/model/prompt hash. Do not cache benchmark answers across dev configurations or hide incurred costs. Keep original basic code, datasets and historical metrics intact. Add advanced dependencies and one-command download/extract/index/run/grade/verify instructions. Fill the existing advanced section of the teacher report when real artifacts exist, preserving the four-section template. Commit public artifacts only, exclude .env and keys.
