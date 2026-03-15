"""Settings endpoints — prompts + config CRUD."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from webseed.api.auth import require_api_key
from webseed.api.deps import get_store
from webseed.ports import PersistencePort

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingUpdate(BaseModel):
    value: str
    description: str = ""


@router.get("")
def list_settings(
    prefix: str | None = None,
    store: PersistencePort = Depends(get_store),
    _key: str = Depends(require_api_key),
) -> list[dict[str, Any]]:
    return store.list_settings(prefix=prefix)


@router.get("/{key:path}")
def get_setting(
    key: str,
    store: PersistencePort = Depends(get_store),
    _key: str = Depends(require_api_key),
) -> dict[str, Any]:
    value = store.get_setting(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return {"key": key, "value": value}


@router.put("/{key:path}")
def update_setting(
    key: str,
    body: SettingUpdate,
    store: PersistencePort = Depends(get_store),
    _key: str = Depends(require_api_key),
) -> dict[str, str]:
    store.upsert_setting(key, body.value, body.description)
    return {"status": "updated", "key": key}
