# Financial RAG Eval Report

This deterministic baseline scores whether retrieval returns the expected source lines.
It is a citation-control test, not an LLM quality claim.

## Summary

- Cases: 4
- Average line recall@k: 100.00%
- Average expected-term coverage@k: 100.00%
- Pass rate: 100.00%

## Cases

### liquidity_short_term_debt_cash: PASS

Question: What source lines show the issuer's short-term debt and cash position?

- Expected lines: 23, 24
- Line recall@k: 100.00%
- Expected-term coverage@k: 100.00%

| Rank | Line | Score | Text |
| ---: | ---: | ---: | --- |
| 1 | 23 | 0.30 | Short-term debt: 18.5 bn |
| 2 | 22 | 0.24 | Total debt: 78.0 bn |
| 3 | 24 | 0.24 | Cash: 12.0 bn |
| 4 | 35 | 0.20 | The issuer uses perpetual debt instruments in part of its financing structure. |
| 5 | 36 | 0.16 | Several subsidiaries provide external guarantees for affiliated infrastructure |

### negative_free_cash_flow: PASS

Question: Where does the note explain negative free cash flow?

- Expected lines: 32, 33
- Line recall@k: 100.00%
- Expected-term coverage@k: 100.00%

| Rank | Line | Score | Text |
| ---: | ---: | ---: | --- |
| 1 | 32 | 0.67 | Free cash flow remained negative because capital expenditure exceeded operating |
| 2 | 31 | 0.53 | Debt growth accelerated after the start of the rail transit expansion plan. |
| 3 | 33 | 0.53 | cash flow. |
| 4 | 25 | 0.33 | Operating cash flow: 5.1 bn |
| 5 | 24 | 0.27 | Cash: 12.0 bn |

### guarantee_exposure: PASS

Question: Which lines mention external guarantees?

- Expected lines: 36, 37
- Line recall@k: 100.00%
- Expected-term coverage@k: 100.00%

| Rank | Line | Score | Text |
| ---: | ---: | ---: | --- |
| 1 | 36 | 0.50 | Several subsidiaries provide external guarantees for affiliated infrastructure |
| 2 | 35 | 0.40 | The issuer uses perpetual debt instruments in part of its financing structure. |
| 3 | 37 | 0.40 | companies. |

### government_support: PASS

Question: Where is government support discussed?

- Expected lines: 12, 13
- Line recall@k: 100.00%
- Expected-term coverage@k: 100.00%

| Rank | Line | Score | Text |
| ---: | ---: | ---: | --- |
| 1 | 12 | 0.33 | strategic importance to the local government and receives recurring government |
| 2 | 13 | 0.33 | support for key projects. |
| 3 | 11 | 0.27 | urban infrastructure projects in a provincial capital region. The issuer has |

## Limitations

- This v0 uses token overlap with one-line neighbor expansion, not embeddings.
- The sample documents are synthetic and public-safe.
- Passing this eval does not prove answer quality; it only checks retrieval of expected evidence lines.
