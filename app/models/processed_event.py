from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy import func

from app.database import Base


class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    id = Column(Integer, primary_key=True)

    event_id = Column(String(36), nullable=False)
    event_type = Column(String, nullable=False)
    correlation_id = Column(String(36), nullable=False)

    processed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            name="uq_processed_events_event_id",
        ),
    )