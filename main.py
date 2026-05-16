from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI
from openai import OpenAI
from pydantic import BaseModel, Field

from database import Base
from database import SessionLocal
from database import engine

from models import IntakeRecord

load_dotenv()

client = OpenAI()
app = FastAPI()

Base.metadata.create_all(bind=engine)

REQUIRED_FIELDS = {
    "policy_number",
    "date_of_loss",
    "description",
}

class IntakeRequest(BaseModel):
    text: str


class IntakeResult(BaseModel):
    claim_type: str
    severity: Literal["low", "medium", "high"]

    policy_number: str | None = None
    date_of_loss: str | None = None
    description: str | None = None

    missing_fields: list[str]

    requires_review: bool
    confidence: float = Field(ge=0, le=1)

@app.get("/health")
def health():
    return {"status": "ok"}

def apply_business_rules(result: IntakeResult) -> IntakeResult:
    missing_fields = []

    for field in REQUIRED_FIELDS:
        value = getattr(result, field)
        if not value:
            missing_fields.append(field)

    result.missing_fields = sorted(missing_fields)

    if result.severity == "high":
        result.requires_review = True

    if missing_fields:
        result.requires_review = True

    if result.confidence < 0.75:
        result.requires_review = True

    return result

@app.post("/intake", response_model=IntakeResult)
def intake(request: IntakeRequest):
    response = client.responses.parse(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You extract structured insurance intake information. "
                    "Extract claim_type, severity, policy_number, date_of_loss, description, and confidence. "
                    "Use null for missing values. "
                    "Do not invent information."
                )
            },
            {
                "role": "user",
                "content": request.text,
            },
        ],
        text_format=IntakeResult,
    )
    extracted = response.output_parsed
    validated = apply_business_rules(extracted)

    db = SessionLocal()

    record = IntakeRecord(
        raw_text=request.text,
        claim_type=validated.claim_type,
        severity=validated.severity,
        policy_number=validated.policy_number,
        date_of_loss=validated.date_of_loss,
        description=validated.description,
        missing_fields=",".join(validated.missing_fields),
        requires_review=validated.requires_review,
        confidence=validated.confidence,
    )

    db.add(record)
    db.commit()

    db.close()

    return validated

@app.get("/intakes")
def get_intakes():
    db = SessionLocal()

    try:
        records = db.query(IntakeRecord).all()

        return [
            {
                "id": record.id,
                "raw_text": record.raw_text,
                "claim_type": record.claim_type,
                "severity": record.severity,
                "policy_number": record.policy_number,
                "date_of_loss": record.date_of_loss,
                "description": record.description,
                "missing_fields": record.missing_fields.split(",") if record.missing_fields else [],
                "requires_review": record.requires_review,
                "confidence": record.confidence,
            }
            for record in records
        ]
    finally:
        db.close()

@app.get("/intakes/review")
def get_review_intakes():
    db = SessionLocal()

    try:
        records = (
            db.query(IntakeRecord)
            .filter(IntakeRecord.requires_review == True)
            .all()
        )

        return [
            {
                "id": record.id,
                "claim_type": record.claim_type,
                "severity": record.severity,
                "policy_number": record.policy_number,
                "date_of_loss": record.date_of_loss,
                "description": record.description,
                "missing_fields": record.missing_fields.split(",") if record.missing_fields else [],
                "confidence": record.confidence,
            }
            for record in records
        ]
    finally:
        db.close()