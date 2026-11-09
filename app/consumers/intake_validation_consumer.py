import json
import os
from datetime import datetime, timezone

import boto3
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import (
    IntakeRecord,
    OutboxEvent,
    ProcessedEvent,
    IntakeValidationAttempt,
)
from app.services.intake_service import validate_intake_text
from app.events.intake_events import IntakeValidationCompleted

load_dotenv()


AWS_PROFILE = os.getenv("AWS_PROFILE")
AWS_REGION = os.getenv("AWS_REGION")
QUEUE_URL = os.getenv("SQS_INTAKE_VALIDATION_QUEUE_URL")

session = boto3.Session(
    profile_name=AWS_PROFILE,
    region_name=AWS_REGION,
)

sqs = session.client("sqs")

def handle_intake_submitted( db, event: dict,):
    aggregate_id = event["aggregate_id"]
    event_id = event["event_id"]
    correlation_id = event["correlation_id"]

    intake = db.get(IntakeRecord, aggregate_id)

    if intake is None:
        raise ValueError(
            f"Intake {aggregate_id} not found for event {event_id}"
        )

    print(f"Handling IntakeSubmitted event {event_id}")
    print(f"Intake ID: {intake.id}")
    print(f"Correlation ID: {correlation_id}")
    print(f"Raw intake text: {intake.raw_text}")

    intake.status = "VALIDATING"
    intake.validation_started_at = datetime.now(timezone.utc)

    validated = validate_intake_text(intake.raw_text)

    intake.claim_type = validated.claim_type
    intake.severity = validated.severity
    intake.policy_number = validated.policy_number
    intake.date_of_loss = validated.date_of_loss
    intake.description = validated.description
    intake.missing_fields = ",".join(validated.missing_fields)
    intake.potential_preexisting_issue = (
        validated.potential_preexisting_issue
    )
    intake.requires_review = validated.requires_review
    intake.confidence = validated.confidence

    intake.status = "VALIDATED"
    intake.validation_completed_at = datetime.now(timezone.utc)

    completion_event = IntakeValidationCompleted(
        aggregate_id=intake.id,
        correlation_id=correlation_id,
        causation_id=event_id,
    )
    outbox_event = OutboxEvent(
        event_id=completion_event.event_id,
        event_type=completion_event.event_type,
        event_version=completion_event.event_version,
        aggregate_type=completion_event.aggregate_type,
        aggregate_id=completion_event.aggregate_id,
        correlation_id=completion_event.correlation_id,
        causation_id=completion_event.causation_id,
        occurred_at=completion_event.occurred_at,
        payload=completion_event.payload,
    )
    db.add(outbox_event)

    print(f"Intake {intake.id} validation completed.")


def receive_one_message():
    response = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10,
        AttributeNames=[
            "ApproximateReceiveCount",
        ],
    )

    messages = response.get("Messages", [])

    if not messages:
        return

    message = messages[0]
    receipt_handle = message["ReceiptHandle"]

    receive_count = message.get(
        "Attributes",
        {},
    ).get(
        "ApproximateReceiveCount",
        "unknown",
    )

    db = None

    try:
        body = json.loads(message["Body"])

        event_id = body["event_id"]
        event_type = body["event_type"]
        correlation_id = body["correlation_id"]

        print(f"SQS receive count: {receive_count}")
        print(f"Received event {event_id}")
        print(f"Event type: {event_type}")
        print(f"Correlation ID: {correlation_id}")

        db = SessionLocal()

        processed_event = db.execute(
            select(ProcessedEvent)
            .where(ProcessedEvent.event_id == event_id)
        ).scalar_one_or_none()

        if processed_event is not None:
            sqs.delete_message(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=receipt_handle,
            )

            print(
                f"Event {event_id} was already processed."
            )
            print(
                "Deleted duplicate message from SQS."
            )
            return

        if event_type == "IntakeSubmitted":
            handle_intake_submitted(
                db=db,
                event=body,
            )
        else:
            raise ValueError(
                f"Unknown event type: {event_type}"
            )

        processed_event = ProcessedEvent(
            event_id=event_id,
            event_type=event_type,
            correlation_id=correlation_id,
        )

        db.add(processed_event)

        try:
            db.commit()

        except IntegrityError:
            db.rollback()

            sqs.delete_message(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=receipt_handle,
            )

            print(
                f"Event {event_id} was already processed "
                "by another consumer."
            )
            print(
                "Deleted duplicate message from SQS."
            )
            return

        sqs.delete_message(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=receipt_handle,
        )

        print(
            f"Recorded event {event_id} as processed."
        )
        print(
            "Deleted message from SQS."
        )


    except Exception as exc:
        if db is not None:
            db.rollback()

        print(
            f"Message processing failed "
            f"(receive count {receive_count}): {exc}"
        )

        # Record the failed attempt in a separate transaction.
        # The original validation transaction has already rolled back.
        try:
            if (
                db is not None
                and isinstance(body, dict)
                and body.get("event_type") == "IntakeSubmitted"
            ):
                attempt = IntakeValidationAttempt(
                    intake_id=body["aggregate_id"],
                    event_id=body["event_id"],
                    correlation_id=body["correlation_id"],
                    attempt_number=int(receive_count),
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )

                db.add(attempt)
                db.commit()

                print(
                    f"Recorded failed validation attempt "
                    f"{receive_count} for intake "
                    f"{body['aggregate_id']}."
                )

        except Exception as exc:
            if db is not None:
                db.rollback()

            print(
                f"Message processing failed "
                f"(receive count {receive_count}): {exc}"
            )

            # Persist the failure separately from the rolled-back
            # validation transaction.
            try:
                if (
                    db is not None
                    and isinstance(body, dict)
                    and body.get("event_type") == "IntakeSubmitted"
                ):
                    attempt = IntakeValidationAttempt(
                        intake_id=body["aggregate_id"],
                        event_id=body["event_id"],
                        correlation_id=body["correlation_id"],
                        attempt_number=int(receive_count),
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                    )

                    db.add(attempt)
                    db.commit()

                    print(
                        f"Recorded failed validation attempt "
                        f"{receive_count} for intake "
                        f"{body['aggregate_id']}."
                    )

            except Exception as logging_exc:
                if db is not None:
                    db.rollback()

                print(
                    f"Failed to record validation attempt: "
                    f"{logging_exc}"
                )

            print(
                "Message was NOT deleted. "
                "SQS will retry it and eventually redrive "
                "it to the DLQ."
            )

        finally:
            if db is not None:
                db.close()


def run_consumer():
    print("Intake validation consumer started.")

    while True:
        receive_one_message()


if __name__ == "__main__":
    run_consumer()