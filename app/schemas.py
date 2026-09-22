from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class FlagCreate(ApiModel):
    key: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{1,63}$")
    description: str = Field(default="", max_length=500)
    enabled: bool = False


class FlagUpdate(ApiModel):
    description: Optional[str] = Field(default=None, max_length=500)  # noqa: UP045
    enabled: Optional[bool] = None  # noqa: UP045

    @model_validator(mode="after")
    def require_a_non_null_change(self) -> FlagUpdate:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Updated fields cannot be null")
        return self


class FlagResponse(ApiModel):
    id: int
    key: str
    description: str
    enabled: bool
    created_at: datetime
    updated_at: datetime


class FlagEvaluationResponse(ApiModel):
    flag: str
    user_id: str
    enabled: bool
    reason: Literal["user_override", "global"]


class OverrideUpsert(ApiModel):
    enabled: bool


class OverrideResponse(ApiModel):
    id: int
    flag_id: int
    user_id: str
    enabled: bool


UserId = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]
