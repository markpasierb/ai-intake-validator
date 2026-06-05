# AI Intake Validator

AI-powered intake validation service built with FastAPI and OpenAI.  
Insurance intake data is often incomplete, inconsistent, and unstructured. This project demonstrates an architecture that uses LLMs for extraction while retaining deterministic business validation and review workflows.
## Features

- Structured extraction from unstructured text
- OpenAI API integration
- Business-rule validation
- Human review escalation
- SQLite persistence

## Tech Stack

- Python
- FastAPI
- OpenAI SDK
- SQLAlchemy
- SQLite

## Running Locally

```bash
python -m uvicorn app.main:app --reload
```

## Example Request
```json
{
  "text": "Customer reports roof damage after hail..."
}
```

## Example Response
```json
{
  "claim_type": "roof_damage",
  "severity": "high",
  "missing_fields": ["policy_number"],
  "requires_review": true,
  "potential_preexisting_issue": false
}
```

## Architecture Notes

The application separates AI-based information extraction from deterministic business logic. OpenAI models are used to extract structured fields from unstructured intake text, while validation and review-escalation rules are enforced within application code.

Added detection of pre-existing issues
