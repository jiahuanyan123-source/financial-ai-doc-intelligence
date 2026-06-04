# Financial RAG Eval Report

This deterministic baseline scores whether retrieval returns the expected source lines.
It is a citation-control test, not an LLM quality claim.

## Summary

- Cases: 4
- Average line recall@k: 87.50%
- Average expected-term coverage@k: 91.67%
- Average source document hit@k: 100.00%
- Average distractor leak rate@k: 5.00%
- Pass rate: 50.00%

## Cases

### north_river_liquidity: FAIL

Question: Which source lines show North River's short-term debt and cash position?

- Expected lines: 23, 24
- Line recall@k: 100.00%
- Expected-term coverage@k: 100.00%
- Source document hit@k: 100.00%
- Distractor leak rate@k: 20.00%

| Rank | Source | Line | Score | Text |
| ---: | --- | ---: | ---: | --- |
| 1 | multi_doc/north_river_target.md | 23 | 0.45 | Short-term debt: 18.5 bn |
| 2 | multi_doc/north_river_target.md | 22 | 0.40 | Total debt: 78.0 bn |
| 3 | multi_doc/north_river_target.md | 24 | 0.40 | Cash: 12.0 bn |
| 4 | multi_doc/east_bay_peer.md | 35 | 0.36 | Liquidity pressure is manageable because cash exceeds short-term debt. |
| 5 | multi_doc/north_river_target.md | 1 | 0.36 | # North River Infrastructure Group - Credit Note |

### north_river_external_guarantees: FAIL

Question: Where does North River disclose external guarantees?

- Expected lines: 36, 37
- Line recall@k: 50.00%
- Expected-term coverage@k: 66.67%
- Source document hit@k: 100.00%
- Distractor leak rate@k: 0.00%

| Rank | Source | Line | Score | Text |
| ---: | --- | ---: | ---: | --- |
| 1 | multi_doc/north_river_target.md | 1 | 0.80 | # North River Infrastructure Group - Credit Note |
| 2 | multi_doc/north_river_target.md | 3 | 0.80 | Issuer: North River Infrastructure Group |
| 3 | multi_doc/north_river_target.md | 10 | 0.80 | North River Infrastructure Group operates toll roads, rail transit assets, and |
| 4 | multi_doc/north_river_target.md | 36 | 0.80 | Several subsidiaries provide external guarantees for affiliated infrastructure |
| 5 | multi_doc/north_river_target.md | 4 | 0.72 | Rating: AAA |

### east_bay_liquidity_comparison: PASS

Question: Which lines show that East Bay cash exceeds short-term debt?

- Expected lines: 35
- Line recall@k: 100.00%
- Expected-term coverage@k: 100.00%
- Source document hit@k: 100.00%
- Distractor leak rate@k: 0.00%

| Rank | Source | Line | Score | Text |
| ---: | --- | ---: | ---: | --- |
| 1 | multi_doc/east_bay_peer.md | 35 | 0.70 | Liquidity pressure is manageable because cash exceeds short-term debt. |
| 2 | multi_doc/east_bay_peer.md | 34 | 0.60 | The issuer has no material external guarantee exposure disclosed in this note. |
| 3 | multi_doc/east_bay_peer.md | 22 | 0.50 | Short-term debt: 9.0 bn |
| 4 | multi_doc/east_bay_peer.md | 21 | 0.44 | Total debt: 54.0 bn |
| 5 | multi_doc/east_bay_peer.md | 23 | 0.44 | Cash: 15.5 bn |

### harbor_city_grant_support: PASS

Question: Which source lines discuss Harbor City's government grants?

- Expected lines: 12, 33
- Line recall@k: 100.00%
- Expected-term coverage@k: 100.00%
- Source document hit@k: 100.00%
- Distractor leak rate@k: 0.00%

| Rank | Source | Line | Score | Text |
| ---: | --- | ---: | ---: | --- |
| 1 | multi_doc/city_utility_distractor.md | 1 | 0.38 | # Harbor City Utility Services - Credit Note |
| 2 | multi_doc/city_utility_distractor.md | 3 | 0.38 | Issuer: Harbor City Utility Services |
| 3 | multi_doc/city_utility_distractor.md | 10 | 0.38 | Harbor City Utility Services operates water supply, wastewater treatment, and |
| 4 | multi_doc/city_utility_distractor.md | 12 | 0.38 | targeted government grants for environmental upgrades. |
| 5 | multi_doc/city_utility_distractor.md | 33 | 0.38 | Government grants support part of the wastewater upgrade program, but the note |

## Limitations

- This v0 uses token overlap with one-line neighbor expansion, not embeddings.
- The sample documents are synthetic and public-safe.
- Passing this eval does not prove answer quality; it only checks retrieval of expected evidence lines.
