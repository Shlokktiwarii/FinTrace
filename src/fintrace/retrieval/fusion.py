from fintrace.retrieval.models import SearchResult


def reciprocal_rank_fusion(
    result_lists: list[list[SearchResult]],
    limit: int = 5,
    k: int = 60,
) -> list[SearchResult]:
    """Combine ranked result lists using Reciprocal Rank Fusion."""
    if limit < 1:
        raise ValueError("Limit must be at least 1")

    if k < 1:
        raise ValueError("RRF k must be at least 1")

    fused_scores: dict[str, float] = {}
    chunks = {}

    for results in result_lists:
        seen_in_list: set[str] = set()

        for rank, result in enumerate(results, start=1):
            chunk_id = result.chunk.chunk_id

            # A chunk contributes at most once per ranking.
            if chunk_id in seen_in_list:
                continue

            seen_in_list.add(chunk_id)

            fused_scores[chunk_id] = (
                fused_scores.get(chunk_id, 0.0)
                + 1.0 / (k + rank)
            )

            chunks.setdefault(chunk_id, result.chunk)

    ranked_ids = sorted(
        fused_scores,
        key=lambda chunk_id: fused_scores[chunk_id],
        reverse=True,
    )

    return [
        SearchResult(
            chunk=chunks[chunk_id],
            score=fused_scores[chunk_id],
        )
        for chunk_id in ranked_ids[:limit]
    ]