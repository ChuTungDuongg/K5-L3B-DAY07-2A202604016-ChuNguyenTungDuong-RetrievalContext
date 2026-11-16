# Round 2 benchmark evidence checks

Gold status: **assistant-proposed, source-verified; learner confirmation pending**. One dedicated benchmark-author assistant prepared this set independently of inference development. These labels are not human-confirmed and are not model-judge results.

## Scope and freeze

The source is World Bank, *World Development Report 2021: Data for Better Lives* (350 physical pages), DOI 10.1596/978-1-4648-1600-0. Source URL: https://documents1.worldbank.org/curated/en/248201616598597113/pdf/World-Development-Report-2021-Data-for-Better-Lives.pdf . Source hash is pinned in freeze.json. Physical page numbers are 1-based; body printed page = physical page minus 20. Page labels are not interchangeable.

Round 2 Test has 30 fresh cases: 6 table, 5 informative diagram/image, 5 chart, 4 multihop, 4 text, and 6 unanswerable. It contains 24 answerable cases and 6 missing-evidence cases. Round 2 Dev preserves the original 18-case Dev byte-for-byte. No old benchmark or source file is changed.

The author compared all proposed target facts with all 48 original cases. overlap_audit.json records the new targets and the closest reused source objects. Sharing a source page/table or a unit qualifier does not by itself reuse an answer fact. No old requested target answer fact or paraphrase was identified. The new Test was not selected by observing round2 model results; no paid API or model judge was used. No difficulty was intentionally reduced to achieve a target score.

## Pixel and evidence procedure

1. Read native PDFium text to locate candidate evidence, then render and inspect original PDF pages. Complex layout is checked against original pixels because a plain text stream can scramble columns and omit colored categorical cells.
2. Assign a single primary group to each case. Diagram cases require relationships between labeled parts; chart cases require numerical marks plus axes or legend. None is a decorative-image or caption-only question.
3. Inspect the full relevant object, including table column headers and notes, chart axis units and legends, diagram stage headers, and text continuation across columns or pages. All normalized boxes use the top-left origin. Every evidence reference has a crop under samples/ and is listed in verification_manifest.json.
4. Recheck arithmetic explicitly: 98−30=68 percentage points; 47−31=16 score points; 75−37=38 percentage points; 27−2.6=24.4 days; 6−1=5 days; 35−8=27 percentage points; 5.60−0.80=4.80 US$/GB/month.
5. Distinguish populations, country averages, published-data percentages, score points, subscriptions per 100 persons, monthly nominal earnings, and unrealized indirect-tax potential. Preserve inequality and conditional language such as “less than one-third,” “proposals,” and “at least.”

## Visual sample links

These are original-source crops, with no generated pixels or edited labels:

- [Color-coded provision table](samples/adv-r2-test-02-e1.png): full table and binding/soft-law/blank legend, WDR 2021 team.
- [Multidimensional legal-framework diagram](samples/adv-r2-test-09-e1.png): intersecting axes and all three legend entries, WDR 2021 team.
- [Broadband subscription chart](samples/adv-r2-test-13-e1.png): four groups plus world, subscriptions-per-100-persons axis, wireless/fixed legend, 2019 note; WDR 2021 team based on ITU data.
- [Two-panel skills/wage chart](samples/adv-r2-test-14-e1.png): net-flow signs and scale versus nominal monthly earnings; ILOSTAT and LinkedIn data as credited in the report.
- [Cross-page technical foundation](samples/adv-r2-test-18-e2.png): Box 8.1 continuation supplying TOGAF, not inferred from a partial first page.

For unlabeled bars, accepted numeric ranges are written into gold and facts. These ranges reflect chart resolution, not uncertainty about metric definitions. Directly printed values and arithmetic retain exact gold values.

## Absence checks

Each of the six unanswerable cases is close to a real report topic but asks for a missing disaggregation, parameter pair, absolute quantity, realized outcome, or dispute-result statistic. The correct answer is exactly “Insufficient evidence.” Related source regions show what is present; their omission alone is not treated as proof of global absence.

absence_search_audit.json records term/phrase variants, all matching physical-page lists, a 350-page scan, subject-specific context pages, and a decision for each case. Search normalization uses Unicode NFKC, lowercase, control/soft-hyphen removal, line-break-hyphen joining, whitespace collapse, and word boundaries. Singular/plural variants are explicit where relevant. Generic hits were checked for relevance; the subject-specific sections, notes, and captions were read in context. No external linked document was imported to fill a gap.

## Limits and grading intent

This is assistant-proposed gold verified against the source, not an independent human audit. Full-text term search is reproducible but cannot mathematically prove absence; pixel/context review supplements it. Some source graphics are low resolution, hence explicit tolerance on unlabeled bars. The report discusses some third-party work; attribution is retained in quoted/cropped source, and the source PDF itself is not duplicated here.

Grade all requested conditions and all claims, with unit/denominator accuracy, arithmetic, physical page, and evidence region coverage. A locator may encompass the full original object or page if it actually includes the required content. A box missing the relevant column, row, axis, legend, or continuation cannot support the answer. An answerable abstention or API error is a failure. Preserve all 30 cases when computing the Test denominator.
