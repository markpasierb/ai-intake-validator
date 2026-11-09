from fastapi import HTTPException
from app.models import IntakeRecord, OutboxEvent
from app.events.intake_events import IntakeSubmitted
from app.schemas import IntakeRequest
from app.schemas import IntakeResult
from app.schemas import IntakeSubmissionResult
from app.schemas import ReviewUpdate
from app.database import SessionLocal

from fastapi import File, UploadFile
from pypdf import PdfReader
from io import BytesIO

from openai import OpenAI

REQUIRED_FIELDS = {
    "policy_number",
    "date_of_loss",
    "description",
}

client = OpenAI()

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


def validate_intake_text(text: str) -> IntakeResult:
    response = client.responses.parse(
        model="gpt-5.4-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You extract structured insurance intake information. "
                    "Extract claim_type, severity, policy_number, date_of_loss, "
                    "description, and confidence. "
                    "Use null for missing values. "
                    "Do not invent information."
                ),
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        text_format=IntakeResult,
    )

    extracted = response.output_parsed

    return apply_business_rules(extracted)


def intake(
    request: IntakeRequest,
    correlation_id: str,
) -> IntakeSubmissionResult:
    db = SessionLocal()

    try:
        record = IntakeRecord(
            raw_text=request.text,
            correlation_id=correlation_id,
            status="SUBMITTED",
        )

        db.add(record)
        db.flush()

        intake_id = record.id

        event = IntakeSubmitted(
            aggregate_id=intake_id,
            correlation_id=correlation_id,
        )

        outbox_event = OutboxEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            event_version=event.event_version,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            occurred_at=event.occurred_at,
            payload=event.payload,
        )

        db.add(outbox_event)

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

    return IntakeSubmissionResult(
        intake_id=intake_id,
        status="SUBMITTED",
        correlation_id=correlation_id,
    )


async def intake_file(file: UploadFile = File(...)):
    contents = await file.read()

    if file.filename.endswith(".txt"):
        text = contents.decode("utf-8")

    elif file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(contents)

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="No readable text found in PDF. Scanned/image PDFs are not supported yet.",
            )

    else:
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .pdf files are supported",
        )

    request = IntakeRequest(text=text)

    return intake(request)

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

def extract_text_from_pdf(contents: bytes) -> str:
    reader = PdfReader(BytesIO(contents))

    pages_text = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages_text.append(text)

    return "\n".join(pages_text)