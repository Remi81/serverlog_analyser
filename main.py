"""Entrypoint minimal pour l'analyseur de logs

Contient les imports recommandés et un squelette FastAPI.
TODOs: ajout du parsing streaming, stockage des jobs, endpoints pour obtenir les résultats.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

import uvicorn
import logging
import re
import os
import io
import pathlib
import tempfile
import asyncio
import aiofiles
import csv
import json
from datetime import datetime, timezone
from collections import Counter, defaultdict
import statistics
from typing import List, Dict, Any, Optional

# Optionnel / recommandé
# import pandas as pd
# import numpy as np

# ---------------------------------
# Configuration de base
# ---------------------------------
logger = logging.getLogger("log_analyser")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="Server Log Analyser", version="0.2", description="Analyse de fichiers de logs serveurs")

# Directory where uploaded logs are stored (created if missing)
UPLOADS_DIR = pathlib.Path("uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# instantiate uploader (module serverlog_analyser.uploader)
from serverlog_analyser.uploader import Uploader
uploader = Uploader(UPLOADS_DIR)

# ---------------------------------
# Models
# ---------------------------------
class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[float] = None

class ParseResult(BaseModel):
    total_requests: int
    status_counts: Dict[str, int]
    top_paths: List[Dict[str, Any]]
    top_ips: List[Dict[str, Any]]
    timings: Dict[str, float]

# In-memory job storage (encapsulated in classes)
import uuid

# Job moved to `serverlog_analyser.jobs.Job` (refactor)
# See serverlog_analyser/jobs.py for implementation


# JobManager moved to `serverlog_analyser.jobs.JobManager` (refactor)
from serverlog_analyser.jobs import JobManager

# instantiate job manager
job_manager = JobManager()
# ---------------------------------
# Helpers
# ---------------------------------
# Uploader.save handles saving uploads to `uploads/` (see serverlog_analyser.uploader.Uploader)
# The old save_upload_to_tempfile has been moved to the Uploader class.

# LogParser moved to `serverlog_analyser.parser.LogParser` (refactor)
# See serverlog_analyser/parser.py for implementation
# ---------------------------------
# Endpoints
# ---------------------------------
@app.get("/api/health")
async def health():
    return {"status": "ok"}

# Serve static frontend mounted at /static to avoid intercepting API routes
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index explicitly at root so POST /upload is not intercepted by the static mount
@app.get("/")
async def root():
    return FileResponse("static/index.html")

# Return a small generic SVG favicon to avoid 404 messages
from fastapi.responses import Response

@app.get("/favicon.ico")
async def favicon():
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'>"
           "<rect width='16' height='16' rx='3' fill='#374151'/>"
           "<text x='50%' y='50%' font-size='10' fill='white' text-anchor='middle' dominant-baseline='central'>L</text>"
           "</svg>")
    return Response(content=svg, media_type='image/svg+xml')

@app.post("/upload")
async def upload(request: 'Request', file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    # debug: log headers and content length if present
    try:
        headers = dict(request.headers)
        logger.info("Upload request headers: %s", {k: headers.get(k) for k in ('content-length', 'content-type')})
    except Exception:
        pass

    logger.info("Upload started: filename=%s", file.filename)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # create job and reserve it before upload
    job = job_manager.create_job(file.filename)
    try:
        tmp_path = await uploader.save(file)
    except Exception as e:
        logger.exception("Upload failed or interrupted: %s", e)
        job.status = "failed"
        job.error = f"upload_error: {e}"
        raise HTTPException(status_code=500, detail=f"Upload failed or interrupted: {e}")

    job.tmp_path = tmp_path
    # record size
    try:
        job.saved_bytes = os.path.getsize(tmp_path)
    except Exception:
        job.saved_bytes = None

    job.status = "uploaded"
    logger.info("Upload complete for job %s: %s bytes", job.job_id, getattr(job, 'saved_bytes', None))

    # launch processing in background
    if background_tasks is not None:
        background_tasks.add_task(job_manager.process_job, job.job_id)
    else:
        job_manager.process_job(job.job_id)

    return JSONResponse({"job_id": job.job_id, "status": job.status, "uploaded_bytes": job.saved_bytes})

@app.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # mark for cancellation
    job.cancel()
    logger.info("Cancel requested for job %s", job_id)
    return JSONResponse({"job_id": job_id, "status": job.status})

@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()

@app.get("/jobs")
async def list_jobs():
    return {jid: job.to_dict() for jid, job in job_manager._jobs.items()}

# ---------------------------------
# Entrypoint
# ---------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info")
