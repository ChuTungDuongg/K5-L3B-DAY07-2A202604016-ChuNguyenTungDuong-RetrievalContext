# Simplify the Day 7 report

Approved by the user in chat: use Dev and Test in the main report, move older versions and failed first test attempt to appendices, retain the teacher's four sections and table columns. The user asked to update related information and previously authorized commit/push main.

Approach: retain the measured data and all historical artifacts in their current paths. Present the final 17-case dev dataset and seven-case test-v2 dataset as Dev and Test. The main report uses three retrieval runs, three dev-agent runs and two test-agent runs. Use the complete baseline rerun because the first attempt had a provider error, disclose that error visibly, and preserve its grades in the history appendix. Do not select based on the higher score.

The alternatives were retaining all historical rows in the main report, which caused the reported confusion, or starting another evaluation cycle, which would add runs and API cost without being needed for this presentation change. The user approved moving the historical detail to appendices.

Keep the chronology caveat: provisional selection used the original dev dataset; the corrected dev evaluation happened after test. Do not imply a new independent experiment. Keep full historical cost accounting distinct from the smaller main-report subset. Do not change labels, run IDs, datasets, agent code, prices or trace bytes. Do not call a paid API.

Update the report generator, report, generated appendices, a machine-readable main-run selection, README, reproduction guide and requirements audit. Verify the template, 14 main test rows, selected runs and token/cost partition, links, stable generator output and absence of changes to historical data.
