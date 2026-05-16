from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

client = OpenAI()
app = FastAPI()


class IntakeRequest(BaseModel):
    text: str


class IntakeResult(BaseModel):
    claim_type: str = Field(description="Short normalized claim type, like roof_damage or water_damage")
    severity: Literal["low", "medium", "high"]
    missing_fields: list[str]
    requires_review: bool
    confidence: float = Field(ge=0, le=1)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/intake", response_model=IntakeResult)
def intake(request: IntakeRequest):
    response = client.responses.parse(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You extract structured insurance intake information. "
                    "Return only data that fits the requested schema. "
                    "If important information is missing, list it in missing_fields. "
                    "Set requires_review to true when the intake is incomplete, ambiguous, or high severity."
                ),
            },
            {
                "role": "user",
                "content": request.text,
            },
        ],
        text_format=IntakeResult,
    )

    return response.output_parsed