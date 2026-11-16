# Simplify Report Implementation Plan

> **For agentic workers:** Execute inline using the already approved design and user request. Use executing-plans for implementation.

**Goal:** Make the main report readable with two split names while retaining verifiable history and cost accounting.

**Architecture:** Generate the main tables from eight explicit existing runs; generate historical grades and first-attempt test details separately; keep the full ledger untouched. Publish a selection JSON to tie the main report to its raw results.

**Tech Stack:** Python standard library and Vietnamese Markdown.

**Spec:** `docs/superpowers/specs/2026-11-16-simplify-report-design.md`

## Global Constraints

Preserve teacher headings/columns, all raw data/labels, identity, error disclosure and chronology. No API calls or benchmark reruns. Commit/push main remains authorized.

## Review Focus

- Baseline rerun must not hide the first provider error.
- Main subset cost must not be called the full historical total.
- Corrected dev after test must not be represented as pre-test selection.
- Historical paths and existing reproduction commands must remain usable.
- Rebuilding reports must retain the simplified presentation.

## Tasks

- [x] Update generator and produce the five-row agent table, 14-row test table, main-run selection and historical appendix.
- [x] Update README, reproduction guidance and requirements audit to match the two main split names and appendices.
- [x] Verify data/metric consistency, report layout, links, subset cost, deterministic generation and Vietnamese prose.
- [x] Confirm raw data and agent code are untouched, commit/push main and refresh the accessible report copy.

Verification: 34 offline tests and artifact verifier passed. Eight main runs and 14 test rows checked; main/history usage totals partition the original 27-run ledger. Rebuilding is deterministic. Raw data, labels, traces, ledger, teacher templates and agent code are unchanged. Fresh read-only review found no material issues. Academic checker only flags two unchanged teacher-template labels. Commit/push and refreshing the accessible copy are the final publication steps.
