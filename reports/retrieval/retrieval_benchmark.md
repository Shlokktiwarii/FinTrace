# FinTrace Retrieval Benchmark

- Generated: 2026-11-12T07:49:53.990848+00:00
- Questions: 80
- Candidate limit: 10
- Cutoffs: 1, 3, 5, 10

| Method | Questions | Mean latency (ms) | Recall@1 | MRR@1 | nDCG@1 | Recall@3 | MRR@3 | nDCG@3 | Recall@5 | MRR@5 | nDCG@5 | Recall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dense | 80 | 323.97 | 0.163 | 0.219 | 0.306 | 0.431 | 0.163 | 0.192 | 0.211 | 0.230 | 0.163 | 0.197 | 0.233 | 0.276 |
| BM25 | 80 | 3.08 | 0.369 | 0.581 | 0.738 | 0.812 | 0.375 | 0.465 | 0.502 | 0.514 | 0.375 | 0.491 | 0.557 | 0.582 |
| Hybrid_RRF | 80 | 355.69 | 0.225 | 0.431 | 0.550 | 0.762 | 0.225 | 0.321 | 0.350 | 0.379 | 0.225 | 0.348 | 0.398 | 0.468 |
| Hybrid_RRF_Reranked | 80 | 8139.54 | 0.444 | 0.706 | 0.738 | 0.762 | 0.450 | 0.573 | 0.582 | 0.585 | 0.450 | 0.604 | 0.618 | 0.626 |

## Interpretation notes

- Compare methods on the same labelled questions and candidate limit.
- Recall@k measures coverage of labelled relevant chunks.
- MRR@k rewards placing the first relevant chunk near the top.
- nDCG@k accounts for the ranking positions of all relevant chunks.
- Latency is measured around the supplied retriever callable; model loading
  and one-time warm-up should happen before invoking this runner.
- A small or single-question dataset is a smoke test, not evidence of general
  retrieval quality. Expand and manually verify the golden set before claims.
