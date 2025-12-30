from uuid import UUID
from fastapi import Header, HTTPException


def get_device_id(x_device_id: str | None = Header(default=None)) -> UUID:
    if not x_device_id:
        raise HTTPException(status_code=400, detail="Missing X-Device-Id header")

    try:
        return UUID(x_device_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid X-Device-Id header (must be UUID)")
