from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(Integer, primary_key=True)

    # Domain event
    event_id = Column(
        String(36),
        nullable=False,
        unique=True,
        index=True,
    )

    event_type = Column(
        String,
        nullable=False,
        index=True,
    )

    event_version = Column(
        Integer,
        nullable=False,
        default=1,
    )

    aggregate_type = Column(
        String,
        nullable=False,
    )

    aggregate_id = Column(
        Integer,
        nullable=False,
        index=True,
    )

    correlation_id = Column(
        String(36),
        nullable=False,
        index=True,
    )

    causation_id = Column(
        String(36),
        nullable=True,
    )

    occurred_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    payload = Column(
        JSONB,
        nullable=False,
    )

    # Publisher / infrastructure state
    published_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    failed_publish_attempts = Column(
        Integer,
        nullable=False,
        default=0,
    )

    next_attempt_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_publish_error = Column(
        Text,
        nullable=True,
    )