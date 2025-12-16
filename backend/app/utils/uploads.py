from __future__ import annotations

from fastapi import UploadFile


async def read_upload_bytes(file: UploadFile) -> bytes:
    return await file.read()
