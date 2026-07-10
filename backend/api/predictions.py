from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Prediction, Project, User
from backend.schemas import PredictionCreate, PredictionResponse
from backend.auth import get_current_user

router = APIRouter(prefix="/projects/{project_id}/predictions", tags=["predictions"])


@router.get("", response_model=list[PredictionResponse])
def list_predictions(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    decision: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    q = db.query(Prediction).filter(Prediction.project_id == project_id)
    if decision:
        q = q.filter(Prediction.decision == decision)
    return q.order_by(Prediction.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=PredictionResponse, status_code=201)
def create_prediction(
    project_id: int,
    payload: PredictionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    prediction = Prediction(
        project_id=project_id,
        **payload.model_dump(),
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


@router.get("/{prediction_id}", response_model=PredictionResponse)
def get_prediction(
    project_id: int,
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id, Prediction.project_id == project_id
    ).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction
