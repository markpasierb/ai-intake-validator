from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True)
class IntakeSubmitted:
    aggregate_id: int
    correlation_id: str

    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = "IntakeSubmitted"
    event_version: int = 1
    aggregate_type: str = "Intake"
    causation_id: str | None = None
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    payload: dict[str, int] = field(init=False)

    def __post_init__(self):
        object.__setattr__(
            self,
            "payload",
            {"intake_id": self.aggregate_id},
        )


@dataclass(frozen=True)
class IntakeValidationCompleted:
    aggregate_id: int
    correlation_id: str
    causation_id: str

    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = "IntakeValidationCompleted"
    event_version: int = 1
    aggregate_type: str = "Intake"
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    payload: dict[str, int] = field(init=False)

    def __post_init__(self):
        object.__setattr__(
            self,
            "payload",
            {"intake_id": self.aggregate_id},
        )