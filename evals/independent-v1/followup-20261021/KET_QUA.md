# RAG quality regression - 2026-10-21

240 pipeline cases in temporary DB/Qdrant stores, not customer data. Ollama is used for model-dependent branches.
Three v2 label edits were approved by the project user; answers are not independently approved.
Regression only, not independent acceptance. Model unchanged; answer review remains mandatory.

## Same-label comparison

Previous run: quality-final-20261021.

| Dataset | Previous (rescored on same labels) | This run | Service errors | p50 / p95 (s) |
|---|---:|---:|---:|---:|
| evals/independent-v1/customer-v2/main | 47/48 | 48/48 | 0 | 5.675 / 7.844 |
| evals/independent-v1/customer-v2/reserve | 11/12 | 12/12 | 0 | 5.159 / 7.762 |
| evals/rag | 48/48 | 48/48 | 0 | 5.304 / 7.683 |
| evals/bt20 | 60/60 | 60/60 | 0 | 6.66 / 9.585 |
| evals/rag-context | 22/24 | 24/24 | 0 | 5.066 / 7.12 |
| evals/rag-documents | 24/24 | 24/24 | 0 | 5.78 / 8.999 |
| evals/rag-policy | 24/24 | 24/24 | 0 | 5.803 / 9.257 |

## Label changes versus runtime changes

OFFLINE rescoring of saved answers, not additional Ollama calls. V1/v2 differ only in labels 024/048/051.

| Runtime | Labels v1 /60 | Labels v2 /60 |
|---|---:|---:|
| baseline-20261021 | 43 | 46 |
| safety-final-20261021 | 44 | 47 |
| quality-final-20261021 | 56 | 58 |
| four-fixes-verified-20261021 | 58 | 60 |

## Gains, regressions and failures

### evals/independent-v1/customer-v2/main

Gained: customer-022.
Regressed: none.
Quotes missing from retrieved chunks: none.

### evals/independent-v1/customer-v2/reserve

Gained: customer-053.
Regressed: none.
Quotes missing from retrieved chunks: none.

### evals/rag

Gained: none.
Regressed: none.
Quotes missing from retrieved chunks: none.

### evals/bt20

Gained: none.
Regressed: none.
Quotes missing from retrieved chunks: none.

### evals/rag-context

Gained: context-005, context-008.
Regressed: none.
Quotes missing from retrieved chunks: none.

### evals/rag-documents

Gained: none.
Regressed: none.
Quotes missing from retrieved chunks: none.

### evals/rag-policy

Gained: none.
Regressed: none.
Quotes missing from retrieved chunks: none.

## Limits and next steps

- Independent answer review is still required; human-review.jsonl remains blank. Label-only approval is recorded separately.
- Freeze code/model/corpus and thresholds before another team authors a new held-out set; these 60 cases are development data.
- Regex and role-block filters cover tested patterns, not arbitrary prompt injection.
- Verbatim quotes do not prove semantic correctness/completeness. One run does not prove model stability.
- Interrupted quality-v1-20261021 results are excluded from final counts.
