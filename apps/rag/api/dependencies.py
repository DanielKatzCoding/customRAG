from typing import Annotated

from fastapi import Depends, Request
from services.facade import IngestFacade, SearchFacade


def get_ingest_facade(request: Request) -> IngestFacade:
    return request.app.state.ingest_facade


def get_search_facade(request: Request) -> SearchFacade:
    return request.app.state.search_facade


IngestDep = Annotated[IngestFacade, Depends(get_ingest_facade)]
SearchDep = Annotated[SearchFacade, Depends(get_search_facade)]
