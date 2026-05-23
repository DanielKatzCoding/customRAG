import logging

from fastapi import APIRouter

from api.dependencies import SearchDep
from api.schemas import SearchRequest, SearchResponse, SearchResultItem

router = APIRouter(prefix="/search", tags=["search"])
logger = logging.getLogger(__name__)


@router.post("", response_model=SearchResponse)
async def search(body: SearchRequest, search_facade: SearchDep) -> SearchResponse:
    results, clean_query = await search_facade.search(
        query=body.query,
        top_k=body.top_k,
        site_key=body.site_key,
    )
    return SearchResponse(
        results=[
            SearchResultItem(
                chunk_id=r.chunk_id,
                url=r.url,
                text=r.text,
                chunk_index=r.chunk_index,
                score=r.score,
                extras=r.extras,
                char_count=r.char_count,
            )
            for r in results
        ],
        query_clean=clean_query,
        total=len(results),
    )
