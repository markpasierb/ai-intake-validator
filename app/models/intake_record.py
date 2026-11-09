from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.database import Base


class IntakeRecord(Base):
    __tablename__ = "intakes"

    id = Column(Integer, primary_key=True, index=True)

    raw_text = Column(Text)

    claim_type = Column(String, nullable=True)
    severity = Column(String, nullable=True)

    policy_number = Column(String, nullable=True)
    date_of_loss = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    missing_fields = Column(Text, nullable=True)

    potential_preexisting_issue = Column(Boolean, nullable=True)
    requires_review = Column(Boolean, nullable=True)

    confidence = Column(Float, nullable=True)

    reviewed = Column(Boolean, default=False)
    reviewer_notes = Column(Text, nullable=True)

    correlation_id = Column(
        String(36),
        nullable=False,
        index=True,
    )

    status = Column(String, nullable=False, default="SUBMITTED")

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    validation_started_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    validation_completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )