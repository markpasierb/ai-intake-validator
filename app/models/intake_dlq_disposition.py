
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


class IntakeDLQDisposition(Base):
    __tablename__ = "intake_dlq_dispositions"

    id = Column(Integer, primary_key=True)

    event_id = Column(String(36), nullable=False)
    intake_id = Column(Integer, nullable=True)
    correlation_id = Column(String(36), nullable=True)

    disposition = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)

    recorded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            name="uq_intake_dlq_disposition_event_id",
        ),
    )
