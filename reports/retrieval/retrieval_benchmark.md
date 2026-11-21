# FinTrace Retrieval Benchmark

- Generated: 2026-11-15T14:59:02.037507+00:00
- Questions: 80
- Candidate limit: 10
- Cutoffs: 1, 3, 5, 10

| Method | Questions | Mean latency (ms) | Recall@1 | MRR@1 | nDCG@1 | Recall@3 | MRR@3 | nDCG@3 | Recall@5 | MRR@5 | nDCG@5 | Recall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Dense | 80 | 313.34 | 0.087 | 0.169 | 0.181 | 0.244 | 0.087 | 0.129 | 0.132 | 0.139 | 0.087 | 0.139 | 0.143 | 0.163 |
| BM25 | 80 | 48.03 | 0.206 | 0.394 | 0.444 | 0.562 | 0.212 | 0.290 | 0.300 | 0.317 | 0.212 | 0.313 | 0.333 | 0.372 |
| Hybrid_RRF | 80 | 361.14 | 0.113 | 0.231 | 0.325 | 0.500 | 0.113 | 0.173 | 0.195 | 0.219 | 0.113 | 0.187 | 0.226 | 0.283 |
| Hybrid_RRF_Reranked | 80 | 7444.44 | 0.256 | 0.469 | 0.500 | 0.500 | 0.263 | 0.354 | 0.362 | 0.362 | 0.263 | 0.380 | 0.393 | 0.393 |

## Interpretation notes

- Compare methods on the same labelled questions and candidate limit.
- Recall@k measures coverage of labelled relevant chunks.
- MRR@k rewards placing the first relevant chunk near the top.
- nDCG@k accounts for the ranking positions of all relevant chunks.
- Latency is measured around the supplied retriever callable; model loading
  and one-time warm-up should happen before invoking this runner.
- A small or single-question dataset is a smoke test, not evidence of general
  retrieval quality. Expand and manually verify the golden set before claims.
