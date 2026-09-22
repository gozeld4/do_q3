from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class FlagCreate(ApiModel):
    key: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,63}$")
    description: str = Field(default="", max_length=500)
    enabled: bool = False


class FlagUpdate(ApiModel):
    description: str | None = Field(default=None, max_length=500)
    enabled: bool | None = None


class FlagResponse(ApiModel):
    id: int
    key: str
    description: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class OverrideUpsert(ApiModel):
    enabled: bool


class OverrideResponse(ApiModel):
    id: int
    flag_id: int
    user_id: str
    enabled: bool
