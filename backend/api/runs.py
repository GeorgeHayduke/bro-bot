from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Run, Project, AuditLog, User
from backend.schemas import RunCreate, RunResponse
from backend.auth import get_current_user, require_role
from backend.tasks import run_experiment

router = APIRouter(prefix="/projects/{project_id}/runs", tags=["runs"])


def _get_project(project_id: int, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_model=list[RunResponse])
def list_runs(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project(project_id, db)
    q = db.query(Run).filter(Run.project_id == project_id)
    if status:
        q = q.filter(Run.status == status)
    return q.order_by(Run.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=RunResponse, status_code=201)
def create_run(
    project_id: int,
    payload: RunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "data_scientist")),
):
    project = _get_project(project_id, db)

    # Auto-name: run-NNN
    existing_count = db.query(Run).filter(Run.project_id == project_id).count()
    name = payload.name or f"run-{existing_count + 1:03d}"

    run = Run(
        project_id=project_id,
        name=name,
        preset=payload.preset,
        feature_selection=payload.feature_selection,
        status="queued",
        created_by=current_user.id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Dispatch Celery task
    run_experiment.delay(run.id)

    db.add(AuditLog(
        user_id=current_user.id, action="run_created",
        entity_type="run", entity_id=run.id,
        details={"project_id": project_id, "preset": run.preset},
    ))
    db.commit()
    return run


@router.get("/{run_id}", response_model=RunResponse)
def get_run(
    project_id: int,
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = db.query(Run).filter(Run.id == run_id, Run.project_id == project_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/{run_id}/promote", response_model=RunResponse)
def promote_to_champion(
    project_id: int,
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "data_scientist")),
):
    run = db.query(Run).filter(Run.id == run_id, Run.project_id == project_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status != "completed":
        raise HTTPException(status_code=400, detail="Only completed runs can be promoted")

    # Unset current champion
    db.query(Run).filter(Run.project_id == project_id, Run.is_champion == True).update({"is_champion": False})
    run.is_champion = True

    # Update project status
    project = _get_project(project_id, db)
    if project.status == "draft":
        project.status = "experimenting"

    db.commit()
    db.refresh(run)

    db.add(AuditLog(
        user_id=current_user.id, action="run_promoted_champion",
        entity_type="run", entity_id=run.id,
        details={"project_id": project_id, "auc": run.metrics.get("auc") if run.metrics else None},
    ))
    db.commit()
    return run


@router.post("/{run_id}/set-challenger", response_model=RunResponse)
def set_challenger(
    project_id: int,
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "data_scientist")),
):
    run = db.query(Run).filter(Run.id == run_id, Run.project_id == project_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status != "completed":
        raise HTTPException(status_code=400, detail="Only completed runs can be set as challenger")
    if run.is_champion:
        raise HTTPException(status_code=400, detail="Champion cannot also be challenger")

    # Unset current challenger
    db.query(Run).filter(Run.project_id == project_id, Run.is_challenger == True).update({"is_challenger": False})
    run.is_challenger = True
    db.commit()
    db.refresh(run)

    db.add(AuditLog(
        user_id=current_user.id, action="run_set_challenger",
        entity_type="run", entity_id=run.id,
    ))
    db.commit()
    return run
