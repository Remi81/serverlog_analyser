"""Module uploader: responsable de la sauvegarde des fichiers uploadés dans `uploads/`."""
from fastapi import UploadFile
import aiofiles
import pathlib
import uuid
import logging
import os
from typing import Optional

logger = logging.getLogger("uploader")

class Uploader:
    def __init__(self, uploads_dir: pathlib.Path):
        self.uploads_dir = pathlib.Path(uploads_dir)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, upload: UploadFile) -> str:
        """Sauvegarde l'UploadFile dans `uploads/` et renvoie le chemin."""
        sanitized = pathlib.Path(upload.filename).name
        dest_name = f"{uuid.uuid4().hex[:8]}_{sanitized}"
        dest_path = self.uploads_dir / dest_name
        total_written = 0
        try:
            async with aiofiles.open(dest_path, "wb") as out_file:
                while True:
                    chunk = await upload.read(1024 * 1024)
                    if not chunk:
                        break
                    await out_file.write(chunk)
                    total_written += len(chunk)
        except Exception as e:
            try:
                dest_path.unlink()
            except Exception:
                pass
            logger.exception("Error saving upload: %s", e)
            raise
        logger.info("Saved upload to %s (%s bytes)", dest_path, total_written)
        return str(dest_path)
