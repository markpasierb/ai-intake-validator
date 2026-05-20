from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import File, UploadFile
from fastapi import HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field

from database import Base
from database import SessionLocal
from database import engine

from models import IntakeRecord
from schemas import IntakeRequest
from schemas import IntakeResult
from schemas import ReviewUpdate
from schemas import IntakeRecordResponse

load_dotenv()

client = OpenAI()
app = FastAPI()

Base.metadata.create_all(bind=engine)

REQUIRED_FIELDS = {
    "policy_number",
    "date_of_loss",
    "description",
}


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

    if result.potential_preexisting_issue:
        result.requires_review = True

    if missing_fields:
        result.requires_review = True

    if result.confidence < 0.75:
        result.requires_review = True

    return result

@app.post("/intake", response_model=IntakeResult)
def intake(request: IntakeRequest):
    response = client.responses.parse(
        model="gpt-5.4-mini",
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

@app.post("/intake/file", response_model=IntakeResult)
async def intake_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
    contents = await file.read()
    text = contents.decode("utf-8")

    request = IntakeRequest(text=text)

    return intake(request)

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
                "potential_preexisting_issue": record.potential_preexisting_issue,
                "reviewed": record.reviewed,
                "reviewer_notes": record.reviewer_notes,
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
            .filter(IntakeRecord.reviewed == False)
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
                "reviewed": record.reviewed,
                "reviewer_notes": record.reviewer_notes,
            }
            for record in records
        ]
    finally:
        db.close()


@app.patch("/intakes/{intake_id}/review")
def update_intake_review(intake_id: int, review: ReviewUpdate):
    db = SessionLocal()

    try:
        record = (
            db.query(IntakeRecord)
            .filter(IntakeRecord.id == intake_id)
            .first()
        )

        if record is None:
            raise HTTPException(status_code=404, detail="Intake not found")

        record.reviewed = review.reviewed
        record.reviewer_notes = review.reviewer_notes

        db.commit()
        db.refresh(record)

        return {
            "id": record.id,
            "reviewed": record.reviewed,
            "reviewer_notes": record.reviewer_notes,
            "requires_review": record.requires_review,
        }
    finally:
        db.close()