import asyncio
import pathlib
import os

from serverlog_analyser.jobs import JobManager
from serverlog_analyser.config import DELETE_UPLOADS_AFTER_PROCESSING


def test_job_processing_and_delete(tmp_path, monkeypatch):
    # create a small log file
    p = tmp_path / "small.log"
    p.write_text('\n'.join(['127.0.0.1 - - "GET /x HTTP/1.1" 200 12 0.1' for _ in range(10)]))

    jm = JobManager()
    job = jm.create_job('small.log', str(p))
    job.tmp_path = str(p)

    # ensure deletion enabled
    monkeypatch.setenv('DELETE_UPLOADS_AFTER_PROCESSING', '1')
    # also ensure module-level constant reflects env var
    import importlib
    import serverlog_analyser.config as cfg
    importlib.reload(cfg)
    # run the processing coroutine directly
    asyncio.run(jm._process_job_async(job.job_id))

    assert job.status == 'done'
    # file should be removed (jobs._process_job_async uses config to delete only in finally via jobs.py)
    assert not p.exists()


def test_job_processing_keep_file(tmp_path, monkeypatch):
    p = tmp_path / "small2.log"
    p.write_text('\n'.join(['127.0.0.1 - - "GET /x HTTP/1.1" 200 12 0.1' for _ in range(5)]))

    jm = JobManager()
    job = jm.create_job('small2.log', str(p))
    job.tmp_path = str(p)

    # disable deletion
    monkeypatch.setenv('DELETE_UPLOADS_AFTER_PROCESSING', '0')
    import importlib
    import serverlog_analyser.config as cfg
    importlib.reload(cfg)

    asyncio.run(jm._process_job_async(job.job_id))

    assert job.status == 'done'
    assert p.exists()
    # cleanup
    p.unlink()
