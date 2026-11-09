
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.database import Base


class IntakeValidationAttempt(Base):
    __tablename__ = "intake_validation_attempts"

    id = Column(Integer, primary_key=True)

    intake_id = Column(Integer, nullable=False, index=True)
    event_id = Column(String(36), nullable=False, index=True)
    correlation_id = Column(String(36), nullable=False, index=True)

    attempt_number = Column(Integer, nullable=False)

    error_type = Column(String(255), nullable=False)
    error_message = Column(Text, nullable=False)

    failed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "attempt_number",
            name="uq_intake_validation_attempt",
        ),
    )
