# Advanced RAG Implementation Plan

> Execute inline within the user's selected source and USD 5 cap. Use independent source/benchmark and final review assistance where the skill requires it.

**Goal:** implement, run and report a multimodal RAG evaluation satisfying ADVANCED.md, with honest bonus eligibility.

**Architecture:** separate advanced package/data/results; native PDF text plus page/region images and visual search descriptions; pgvector plus lexical ranking; model-driven evidence loop; frozen benchmark and strict evaluation.

**Tech stack:** Python, PDFium/pdfplumber or verified equivalent, existing SentenceTransformer/pgvector, OpenAI Responses API, JSON/Markdown.

**Spec:** docs/superpowers/specs/2026-11-16-advanced-rag-design.md

## Constraints and review focus

- User selected the 350-page World Bank document and USD 5 cap.
- Never overwrite basic A/B or historical data. No keys in Git.
- Index all useful content and report extraction failures, not benchmark-only pages.
- Keep gold out of inference; freeze dataset before dev and pipeline before test.
- Count all 30 test cases including provider errors; no cherry-picked reruns.
- Check charts/tables/diagram facts against original pixels and source locators.

## Tasks

- [ ] Prepare source manifest, complete page extraction/regions and reproducible source verification.
- [ ] Prepare and freeze the 18-case Dev and 30-case Test benchmarks with source evidence.
- [ ] Implement budget ledger, multimodal index, retrieval/inspect/answer loop and behavioral tests.
- [ ] Run source extraction/indexing within cap, inspect coverage and original visual samples.
- [ ] Run two Dev configurations, label/check evidence and freeze selection.
- [ ] Run all Test once, review every case, retain failures and report strict group metrics.
- [ ] Update teacher advanced report section, reproduction and cost ledger, verify artifacts/secrets, obtain final review, commit/push main.
