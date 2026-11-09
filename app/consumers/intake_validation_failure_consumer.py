
import json
import os
import time

import boto3
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import IntakeRecord, IntakeDLQDisposition


load_dotenv()

AWS_PROFILE = os.getenv("AWS_PROFILE")
AWS_REGION = os.getenv("AWS_REGION")
QUEUE_URL = os.getenv("SQS_INTAKE_VALIDATION_DLQ_URL")

session = boto3.Session(
    profile_name=AWS_PROFILE,
    region_name=AWS_REGION,
)

sqs = session.client("sqs")


def process_dlq_event(db, event):
    event_id = event["event_id"]
    event_type = event["event_type"]
    intake_id = event["aggregate_id"]
    correlation_id = event["correlation_id"]

    if event_type != "IntakeSubmitted":
        raise ValueError(
            f"Unexpected DLQ event type: {event_type}"
        )

    existing = db.execute(
        select(IntakeDLQDisposition).where(
            IntakeDLQDisposition.event_id == event_id
        )
    ).scalar_one_or_none()

    if existing is not None:
        print(f"DLQ event {event_id} already recorded.")
        return

    intake = db.get(IntakeRecord, intake_id)

    if intake is None:
        disposition = "ORPHANED"
        details = f"Intake {intake_id} does not exist."

    elif intake.status == "VALIDATED":
        disposition = "ALREADY_VALIDATED"
        details = (
            f"Intake {intake_id} was already validated."
        )

    else:
        disposition = "VALIDATION_FAILED"
        details = (
            "Automatic validation exhausted its "
            "SQS retry policy."
        )

        intake.status = "VALIDATION_FAILED"

    record = IntakeDLQDisposition(
        event_id=event_id,
        intake_id=intake_id,
        correlation_id=correlation_id,
        disposition=disposition,
        details=details,
    )

    db.add(record)

    print(
        f"DLQ disposition for event {event_id}: "
        f"{disposition}"
    )


def receive_one_message():
    response = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10,
    )

    messages = response.get("Messages", [])

    if not messages:
        return

    message = messages[0]
    receipt_handle = message["ReceiptHandle"]

    db = SessionLocal()

    try:
        event = json.loads(message["Body"])

        process_dlq_event(
            db=db,
            event=event,
        )

        db.commit()

        sqs.delete_message(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=receipt_handle,
        )

        print("DLQ message acknowledged.")

    except IntegrityError:
        db.rollback()

        print(
            "DLQ disposition uniqueness conflict. "
            "Message retained for retry."
        )

    except Exception as exc:
        db.rollback()

        print(f"DLQ processing failed: {exc}")
        print("Message retained in DLQ.")

    finally:
        db.close()


def run_consumer():
    if not QUEUE_URL:
        raise RuntimeError(
            "SQS_INTAKE_VALIDATION_DLQ_URL is not configured."
        )

    print("Intake validation DLQ consumer started.")

    while True:
        try:
            receive_one_message()
        except Exception as exc:
            print(f"DLQ polling error: {exc}")
            time.sleep(5)


if __name__ == "__main__":
    run_consumer()
