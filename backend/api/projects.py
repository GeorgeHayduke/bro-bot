from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import Project, Run, AuditLog, User
from backend.schemas import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectSummary
from backend.auth import get_current_user, require_role

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectSummary])
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Project)
    if status:
        q = q.filter(Project.status == status)
    projects = q.order_by(Project.updated_at.desc()).offset(skip).limit(limit).all()

    results = []
    for p in projects:
        run_count = db.query(func.count(Run.id)).filter(Run.project_id == p.id).scalar()
        champion = db.query(Run).filter(Run.project_id == p.id, Run.is_champion == True).first()
        champion_auc = champion.metrics.get("auc") if champion and champion.metrics else None
        latest_run = db.query(Run).filter(Run.project_id == p.id).order_by(Run.created_at.desc()).first()

        summary = ProjectSummary.model_validate(p)
        summary.run_count = run_count
        summary.champion_auc = champion_auc
        summary.latest_run_name = latest_run.name if latest_run else None
        results.append(summary)
    return results


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "data_scientist")),
):
    existing = db.query(Project).filter(Project.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project name already exists")

    project = Project(
        **payload.model_dump(),
        created_by=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    db.add(AuditLog(
        user_id=current_user.id, action="project_created",
        entity_type="project", entity_id=project.id,
        details={"name": project.name},
    ))
    db.commit()
    return project


@router.get("/{project_id}", response_model=ProjectSummary)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    run_count = db.query(func.count(Run.id)).filter(Run.project_id == project.id).scalar()
    champion = db.query(Run).filter(Run.project_id == project.id, Run.is_champion == True).first()
    champion_auc = champion.metrics.get("auc") if champion and champion.metrics else None
    latest_run = db.query(Run).filter(Run.project_id == project.id).order_by(Run.created_at.desc()).first()

    summary = ProjectSummary.model_validate(project)
    summary.run_count = run_count
    summary.champion_auc = champion_auc
    summary.latest_run_name = latest_run.name if latest_run else None
    return summary


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "data_scientist")),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)

    db.add(AuditLog(
        user_id=current_user.id, action="project_updated",
        entity_type="project", entity_id=project.id,
        details=update_data,
    ))
    db.commit()
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.add(AuditLog(
        user_id=current_user.id, action="project_deleted",
        entity_type="project", entity_id=project.id,
        details={"name": project.name},
    ))
    db.delete(project)
    db.commit()
