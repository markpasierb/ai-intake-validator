from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from app.database import Base


class IntakeRecord(Base):
    __tablename__ = "intakes"

    id = Column(Integer, primary_key=True, index=True)

    raw_text = Column(Text)

    claim_type = Column(String)
    severity = Column(String)

    policy_number = Column(String, nullable=True)
    date_of_loss = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    missing_fields = Column(Text)

    potential_preexisting_issue = Column(Boolean)
    requires_review = Column(Boolean)

    confidence = Column(Float)

    reviewed = Column(Boolean, default=False)
    reviewer_notes = Column(Text, nullable=True)