import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.config import settings
from backend.database import get_db
from backend.models import Dataset, DatasetVersion, Project, AuditLog, User
from backend.schemas import DatasetCreate, DatasetResponse, DatasetVersionResponse
from backend.auth import get_current_user, require_role
from backend.tasks import profile_dataset

router = APIRouter(prefix="/projects/{project_id}/datasets", tags=["datasets"])


def _get_project(project_id: int, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_model=list[DatasetResponse])
def list_datasets(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project(project_id, db)
    return db.query(Dataset).filter(Dataset.project_id == project_id).order_by(Dataset.created_at.desc()).all()


@router.post("", response_model=DatasetResponse, status_code=201)
def create_dataset(
    project_id: int,
    payload: DatasetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "data_scientist")),
):
    _get_project(project_id, db)
    dataset = Dataset(
        project_id=project_id,
        name=payload.name,
        source_type=payload.source_type,
        filepath=payload.filepath,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    db.add(AuditLog(
        user_id=current_user.id, action="dataset_created",
        entity_type="dataset", entity_id=dataset.id,
    ))
    db.commit()
    return dataset


@router.post("/upload", response_model=DatasetResponse, status_code=201)
async def upload_dataset(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "data_scientist")),
):
    _get_project(project_id, db)

    upload_dir = os.path.join(settings.storage_path, "uploads", str(project_id))
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    dataset = Dataset(
        project_id=project_id,
        name=file.filename,
        source_type="upload",
        filepath=filepath,
        file_size=len(content),
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    # Create initial version and trigger profiling
    version = DatasetVersion(dataset_id=dataset.id, version_num=1)
    db.add(version)
    db.commit()
    db.refresh(version)
    profile_dataset.delay(dataset.id, version.id)

    db.add(AuditLog(
        user_id=current_user.id, action="dataset_uploaded",
        entity_type="dataset", entity_id=dataset.id,
        details={"filename": file.filename, "size": len(content)},
    ))
    db.commit()
    return dataset


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    project_id: int,
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.project_id == project_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.get("/{dataset_id}/versions", response_model=list[DatasetVersionResponse])
def list_versions(
    project_id: int,
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.project_id == project_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id).order_by(DatasetVersion.version_num.desc()).all()


@router.get("/{dataset_id}/profile", response_model=DatasetVersionResponse)
def get_profile(
    project_id: int,
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.project_id == project_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    version = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id
    ).order_by(DatasetVersion.version_num.desc()).first()
    if not version:
        raise HTTPException(status_code=404, detail="No profile available")
    return version
