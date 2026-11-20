# Financial RAG Eval Report

Retriever: `embedding`

This deterministic baseline scores whether retrieval returns the expected source lines.
It is a citation-control test, not an LLM quality claim.

## Summary

- Cases: 4
- Average line recall@k: 100.00%
- Average expected-term coverage@k: 100.00%
- Average source document hit@k: 100.00%
- Average distractor leak rate@k: 0.00%
- Pass rate: 100.00%

## Cases

### north_river_liquidity: PASS

Question: Which source lines show North River's short-term debt and cash position?

- Expected lines: 23, 24
- Line recall@k: 100.00%
- Expected-term coverage@k: 100.00%
- Source document hit@k: 100.00%
- Distractor leak rate@k: 0.00%

| Rank | Source | Line | Score | Text |
| ---: | --- | ---: | ---: | --- |
| 1 | multi_doc/north_river_target.md | 23 | 0.52 | Short-term debt: 18.5 bn |
| 2 | multi_doc/north_river_target.md | 5 | 0.42 | Industry: Transportation Infrastructure |
| 3 | multi_doc/north_river_target.md | 22 | 0.42 | Total debt: 78.0 bn |
| 4 | multi_doc/north_river_target.md | 24 | 0.42 | Cash: 12.0 bn |
| 5 | multi_doc/north_river_target.md | 31 | 0.40 | Debt growth accelerated after the start of the rail transit expansion plan. |

### north_river_external_guarantees: PASS

Question: Where does North River disclose external guarantees?

- Expected lines: 36, 37
- Line recall@k: 100.00%
- Expected-term coverage@k: 100.00%
- Source document hit@k: 100.00%
- Distractor leak rate@k: 0.00%

| Rank | Source | Line | Score | Text |
| ---: | --- | ---: | ---: | --- |
| 1 | multi_doc/north_river_target.md | 36 | 0.62 | Several subsidiaries provide external guarantees for affiliated infrastructure |
| 2 | multi_doc/north_river_target.md | 18 | 0.57 | ## Financial Summary |
| 3 | multi_doc/north_river_target.md | 5 | 0.54 | Industry: Transportation Infrastructure |
| 4 | multi_doc/north_river_target.md | 37 | 0.51 | companies. |
| 5 | multi_doc/north_river_target.md | 22 | 0.50 | Total debt: 78.0 bn |

### east_bay_liquidity_comparison: PASS

Question: Which lines show that East Bay cash exceeds short-term debt?

- Expected lines: 35
- Line recall@k: 100.00%
- Expected-term coverage@k: 100.00%
- Source document hit@k: 100.00%
- Distractor leak rate@k: 0.00%

| Rank | Source | Line | Score | Text |
| ---: | --- | ---: | ---: | --- |
| 1 | multi_doc/east_bay_peer.md | 35 | 0.54 | Liquidity pressure is manageable because cash exceeds short-term debt. |
| 2 | multi_doc/east_bay_peer.md | 22 | 0.46 | Short-term debt: 9.0 bn |
| 3 | multi_doc/east_bay_peer.md | 34 | 0.43 | The issuer has no material external guarantee exposure disclosed in this note. |
| 4 | multi_doc/east_bay_peer.md | 30 | 0.40 | Debt growth remained stable because most park construction is near completion. |
| 5 | multi_doc/east_bay_peer.md | 24 | 0.38 | Operating cash flow: 4.4 bn |

### harbor_city_grant_support: PASS

Question: Which source lines discuss Harbor City's government grants?

- Expected lines: 12, 33
- Line recall@k: 100.00%
- Expected-term coverage@k: 100.00%
- Source document hit@k: 100.00%
- Distractor leak rate@k: 0.00%

| Rank | Source | Line | Score | Text |
| ---: | --- | ---: | ---: | --- |
| 1 | multi_doc/city_utility_distractor.md | 33 | 0.43 | Government grants support part of the wastewater upgrade program, but the note |
| 2 | multi_doc/city_utility_distractor.md | 34 | 0.34 | does not assume extraordinary rescue support. |
| 3 | multi_doc/city_utility_distractor.md | 12 | 0.32 | targeted government grants for environmental upgrades. |
| 4 | multi_doc/city_utility_distractor.md | 10 | 0.29 | Harbor City Utility Services operates water supply, wastewater treatment, and |
| 5 | multi_doc/city_utility_distractor.md | 15 | 0.27 | issuers. Capital expenditure focuses on treatment capacity and pipeline renewal. |

## Limitations

- This embedding run uses a deterministic local hashing backend, not a neural embedding model or external API.
- The sample documents are synthetic and public-safe.
- Passing this eval does not prove answer quality; it only checks retrieval of expected evidence lines.
