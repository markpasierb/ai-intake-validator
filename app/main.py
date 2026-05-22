from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, UploadFile

from app.database import Base, engine
from app.schemas import IntakeRequest, IntakeResult, ReviewUpdate

from app.services.intake_service import (
    health,
    intake,
    intake_file,
    get_intakes,
    get_review_intakes,
    update_intake_review,
)

app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_route():
    return health()


@app.post("/intake", response_model=IntakeResult)
def intake_route(request: IntakeRequest):
    return intake(request)


@app.post("/intake/file", response_model=IntakeResult)
async def intake_file_route(file: UploadFile = File(...)):
    return await intake_file(file)


@app.get("/intakes")
def get_intakes_route():
    return get_intakes()


@app.get("/intakes/review")
def get_review_intakes_route():
    return get_review_intakes()


@app.patch("/intakes/{intake_id}/review")
def update_intake_review_route(intake_id: int, review: ReviewUpdate):
    return update_intake_review(intake_id, review)