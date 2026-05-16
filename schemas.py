from typing import Literal

from pydantic import BaseModel, Field


class IntakeRequest(BaseModel):
    text: str


class IntakeResult(BaseModel):
    claim_type: str
    severity: Literal["low", "medium", "high"]

    policy_number: str | None = None
    date_of_loss: str | None = None
    description: str | None = None
    potential_preexisting_issue: bool

    missing_fields: list[str]

    requires_review: bool
    confidence: float = Field(ge=0, le=1)


class IntakeRecordResponse(IntakeResult):
    id: int
    raw_text: str