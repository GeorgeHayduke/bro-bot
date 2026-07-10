from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Label, Prediction, Project, AuditLog, User
from backend.schemas import LabelCreate, LabelResponse
from backend.auth import get_current_user

router = APIRouter(tags=["labels"])


@router.post(
    "/predictions/{prediction_id}/labels",
    response_model=LabelResponse,
    status_code=201,
)
def create_label(
    prediction_id: int,
    payload: LabelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")

    if payload.label not in ("fraud", "legit", "skip"):
        raise HTTPException(status_code=400, detail="Label must be 'fraud', 'legit', or 'skip'")

    label = Label(
        prediction_id=prediction_id,
        analyst_id=current_user.id,
        label=payload.label,
    )
    db.add(label)
    db.commit()
    db.refresh(label)

    db.add(AuditLog(
        user_id=current_user.id, action="label_created",
        entity_type="prediction", entity_id=prediction_id,
        details={"label": payload.label},
    ))
    db.commit()
    return label


@router.get(
    "/projects/{project_id}/labels",
    response_model=list[LabelResponse],
)
def list_labels(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    labels = (
        db.query(Label)
        .join(Prediction, Prediction.id == Label.prediction_id)
        .filter(Prediction.project_id == project_id)
        .order_by(Label.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return labels
