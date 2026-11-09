import json
import os
import time

import boto3
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.sql import func
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.models import OutboxEvent


load_dotenv()


AWS_PROFILE = os.getenv("AWS_PROFILE")
AWS_REGION = os.getenv("AWS_REGION")
INTAKE_VALIDATION_QUEUE_URL = os.getenv("SQS_INTAKE_VALIDATION_QUEUE_URL")
INTAKE_VALIDATION_COMPLETED_QUEUE_URL = os.getenv( "SQS_INTAKE_VALIDATION_COMPLETED_QUEUE_URL")
QUEUE_BY_EVENT_TYPE = {
    "IntakeSubmitted": INTAKE_VALIDATION_QUEUE_URL,
    "IntakeValidationCompleted": INTAKE_VALIDATION_COMPLETED_QUEUE_URL,
}

BATCH_SIZE = 5
POLL_INTERVAL_SECONDS = 5

def get_retry_delay(attempt_number: int) -> timedelta:
    if attempt_number == 1:
        return timedelta(seconds=5)

    if attempt_number == 2:
        return timedelta(seconds=30)

    return timedelta(minutes=2)


def publish_pending_outbox_events():
    session = boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION,
    )

    sqs = session.client("sqs")

    db = SessionLocal()

    try:
        events = db.execute(
            select(OutboxEvent)
            .where(
                OutboxEvent.published_at.is_(None),
                (
                    OutboxEvent.next_attempt_at.is_(None)
                    | (OutboxEvent.next_attempt_at <= func.now())
                ),
            )
            .order_by(OutboxEvent.id)
            .limit(BATCH_SIZE)
        ).scalars().all()

        if not events:
            return

        for event in events:
            message = {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "event_version": event.event_version,
                "aggregate_type": event.aggregate_type,
                "aggregate_id": event.aggregate_id,
                "correlation_id": event.correlation_id,
                "causation_id": event.causation_id,
                "occurred_at": event.occurred_at.isoformat(),
                "payload": event.payload,
            }

            try:
                queue_url = QUEUE_BY_EVENT_TYPE.get(event.event_type)

                if queue_url is None:
                    raise ValueError(
                        f"No SQS route configured for event type "
                        f"{event.event_type}"
                    )
                response = sqs.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps(message),
                )

            except Exception as exc:
                event.failed_publish_attempts += 1
                event.last_publish_error = str(exc)
                event.next_attempt_at = (
                    datetime.now(timezone.utc)
                    + get_retry_delay(event.failed_publish_attempts)
                )

                db.commit()

                print(
                    f"Failed to publish event {event.event_id}; "
                    f"failed attempt {event.failed_publish_attempts}"
                )
                print(f"Next attempt at: {event.next_attempt_at}")

                continue

            event.published_at = func.now()
            event.last_publish_error = None
            event.next_attempt_at = None

            db.commit()

            print(f"Published event {event.event_id}")
            print(f"SQS MessageId: {response['MessageId']}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def run_publisher():
    print("Outbox publisher started.")

    while True:
        publish_pending_outbox_events()
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_publisher()