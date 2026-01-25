"""Module jobs: Job and JobManager."""
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from .parser import LogParser

logger = logging.getLogger("jobs")

class Job:
    def __init__(self, job_id: str, filename: str, tmp_path: Optional[str] = None):
        self.job_id = job_id
        self.filename = filename
        self.tmp_path = tmp_path
        self.status = "queued"
        self.progress = 0.0
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.cancel_requested: bool = False
        self.saved_bytes: Optional[int] = None
        self.bytes_read: Optional[int] = None
        self.lines_parsed: Optional[int] = None

    def cancel(self):
        self.cancel_requested = True
        self.status = "cancelling"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "filename": self.filename,
            "status": self.status,
            "progress": self.progress,
            "saved_bytes": self.saved_bytes,
            "bytes_read": self.bytes_read,
            "lines_parsed": self.lines_parsed,
            "result": self.result,
            "error": self.error,
        }

class JobManager:
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        # main event loop, set at FastAPI startup so we can schedule from worker threads
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set the event loop to be used for scheduling jobs from other threads."""
        self._loop = loop

    def create_job(self, filename: str, tmp_path: Optional[str] = None) -> Job:
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        job = Job(job_id, filename, tmp_path)
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def _update_progress(self, job: Job, value: Any):
        if isinstance(value, dict):
            job.progress = value.get("progress", job.progress)
            job.bytes_read = value.get("bytes_read", job.bytes_read)
            job.lines_parsed = value.get("lines_parsed", job.lines_parsed)
        else:
            try:
                job.progress = float(value)
            except Exception:
                pass

    async def _process_job_async(self, job_id: str):
        job = self.get_job(job_id)
        if not job:
            logger.error("Job not found: %s", job_id)
            return
        logger.info("Starting job %s (file=%s)", job_id, job.filename)
        job.status = "processing"
        job.progress = 0.0
        try:
            result = await LogParser.parse_file(
                job.tmp_path,
                progress_callback=lambda p: self._update_progress(job, p),
                should_cancel=lambda: job.cancel_requested,
            )
            job.result = result
            job.status = "done"
            job.progress = 1.0
            logger.info("Job %s done", job_id)
        except asyncio.CancelledError:
            logger.info("Job %s cancelled by user", job_id)
            job.status = "cancelled"
        except Exception as e:
            logger.exception("Job processing failed: %s", e)
            job.status = "failed"
            job.error = str(e)
        finally:
            # remove the uploaded tempfile after processing to save disk (controlled by config)
            try:
                from .config import DELETE_UPLOADS_AFTER_PROCESSING
                if (DELETE_UPLOADS_AFTER_PROCESSING) and job and job.tmp_path:
                    import os
                    if os.path.exists(job.tmp_path):
                        os.remove(job.tmp_path)
                        logger.info("Removed temporary file for job %s: %s", job_id, job.tmp_path)
                    job.tmp_path = None
            except Exception as e:
                logger.exception("Failed to remove temporary file for job %s: %s", job_id, e)

    def process_job(self, job_id: str):
        # If called from an async context with a running loop, schedule directly
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._process_job_async(job_id))
            logger.info("Scheduled job %s with running loop", job_id)
            return
        except RuntimeError:
            pass

        # If a main loop was set (FastAPI startup), submit the coroutine thread-safely
        if self._loop is not None:
            try:
                asyncio.run_coroutine_threadsafe(self._process_job_async(job_id), self._loop)
                logger.info("Scheduled job %s via run_coroutine_threadsafe", job_id)
                return
            except Exception as e:
                logger.exception("Failed to schedule job %s via run_coroutine_threadsafe: %s", job_id, e)

        # Last resort: create a background thread with its own event loop to run the job
        try:
            import threading

            def _run():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self._process_job_async(job_id))
                finally:
                    loop.close()

            t = threading.Thread(target=_run, daemon=True)
            t.start()
            logger.info("Scheduled job %s on new thread loop", job_id)
        except Exception as e:
            logger.exception("Failed to schedule job %s: %s", job_id, e)
            job = self.get_job(job_id)
            if job:
                job.status = "failed"
                job.error = f"scheduling_error: {e}"
