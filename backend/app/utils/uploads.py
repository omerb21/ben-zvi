from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import AsyncGenerator

from fastapi import UploadFile


async def read_upload_bytes(file: UploadFile) -> bytes:
    return await file.read()


def save_upload_to_temp_file(file: UploadFile) -> Path:
    """Save an uploaded file to a temporary file on disk.

    Returns the path to the temporary file. The caller is responsible for
    deleting the file when done.
    """
    suffix = Path(file.filename).suffix if file.filename else ".tmp"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        return Path(tmp.name)
