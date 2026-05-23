import logging
import uuid
from pathlib import Path

from core.utils import safe_name
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from models.document import IngestJob
from services.facade import IngestFacade

from api.dependencies import IngestDep
from api.schemas import (
    IngestByPathsRequest,
    IngestByUrlsRequest,
    IngestResponse,
    IngestStatusResponse,
)

router = APIRouter(prefix="/ingest", tags=["ingest"])
logger = logging.getLogger(__name__)


def _resolve_paths(urls: list[str], output_dir: Path) -> list[Path]:
    paths = []
    for url in urls:
        candidate = output_dir / f"{safe_name(url)}.json"
        if not candidate.exists():
            logger.warning("File not found for URL %s, skipping", url)
        else:
            paths.append(candidate)
    return paths


async def _run_ingest(
    file_paths: list[Path],
    job: IngestJob,
    ingest_facade: IngestFacade,
    ingest_running_flag: dict,
) -> None:
    job.status = "running"
    ingest_running_flag["active"] = True
    try:
        for fp in file_paths:
            if not fp.exists():
                logger.warning("Skipping missing file: %s", fp)
                continue
            try:
                await ingest_facade.ingest_file(fp, job)
            except Exception:
                logger.exception("Error ingesting %s", fp)
        job.status = "completed"
    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
        logger.exception("Ingest job %s failed", job.job_id)
    finally:
        ingest_running_flag["active"] = False


@router.post("", response_model=IngestResponse, status_code=202)
async def ingest_by_paths(
    body: IngestByPathsRequest,
    background_tasks: BackgroundTasks,
    ingest_facade: IngestDep,
    request: Request,
) -> IngestResponse:
    paths = [Path(p) for p in body.file_paths]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise HTTPException(status_code=422, detail=f"Files not found: {missing}")

    job_id = str(uuid.uuid4())
    job = IngestJob(job_id=job_id, file_count=len(paths))
    request.app.state.jobs[job_id] = job

    background_tasks.add_task(_run_ingest, paths, job, ingest_facade, request.app.state.ingest_running)
    return IngestResponse(job_id=job_id, message="Ingestion started", file_count=len(paths))


@router.post("/urls", response_model=IngestResponse, status_code=202)
async def ingest_by_urls(
    body: IngestByUrlsRequest,
    background_tasks: BackgroundTasks,
    ingest_facade: IngestDep,
    request: Request,
) -> IngestResponse:
    output_dir = Path(request.app.state.settings.output_dir)
    paths = _resolve_paths(body.urls, output_dir)
    if not paths:
        raise HTTPException(status_code=422, detail="No matching files found for the provided URLs")

    job_id = str(uuid.uuid4())
    job = IngestJob(job_id=job_id, file_count=len(paths))
    request.app.state.jobs[job_id] = job

    background_tasks.add_task(_run_ingest, paths, job, ingest_facade, request.app.state.ingest_running)
    return IngestResponse(job_id=job_id, message="Ingestion started", file_count=len(paths))


@router.post("/all", response_model=IngestResponse, status_code=202)
async def ingest_all(
    background_tasks: BackgroundTasks,
    ingest_facade: IngestDep,
    request: Request,
) -> IngestResponse:
    if request.app.state.ingest_running.get("active", False):
        raise HTTPException(status_code=409, detail="An ingest job is already running")

    output_dir = Path(request.app.state.settings.output_dir)
    if not output_dir.exists():
        raise HTTPException(status_code=422, detail=f"Output directory not found: {output_dir}")

    paths = sorted(output_dir.glob("*.json"))
    if not paths:
        raise HTTPException(status_code=422, detail=f"No JSON files found in {output_dir}")

    job_id = str(uuid.uuid4())
    job = IngestJob(job_id=job_id, file_count=len(paths))
    request.app.state.jobs[job_id] = job

    background_tasks.add_task(_run_ingest, paths, job, ingest_facade, request.app.state.ingest_running)
    return IngestResponse(job_id=job_id, message="Ingestion started", file_count=len(paths))


@router.get("/{job_id}", response_model=IngestStatusResponse)
async def get_job_status(job_id: str, request: Request) -> IngestStatusResponse:
    job: IngestJob | None = request.app.state.jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return IngestStatusResponse(
        job_id=job.job_id,
        status=job.status,
        file_count=job.file_count,
        chunks_ingested=job.chunks_ingested,
        error=job.error,
    )
