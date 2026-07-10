from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.database import get_db
from backend.models import Alert, Project, AuditLog, User
from backend.schemas import AlertResponse, AlertUpdate
from backend.auth import get_current_user

router = APIRouter(tags=["monitoring"])


@router.get("/projects/{project_id}/alerts", response_model=list[AlertResponse])
def list_alerts(
    project_id: int,
    status: str = Query(None),
    severity: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    q = db.query(Alert).filter(Alert.project_id == project_id)
    if status:
        q = q.filter(Alert.status == status)
    if severity:
        q = q.filter(Alert.severity == severity)
    return q.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()


@router.put("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.status != "open":
        raise HTTPException(status_code=400, detail="Alert is not open")

    alert.status = "acknowledged"
    db.commit()
    db.refresh(alert)

    db.add(AuditLog(
        user_id=current_user.id, action="alert_acknowledged",
        entity_type="alert", entity_id=alert.id,
    ))
    db.commit()
    return alert


@router.put("/alerts/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "resolved"
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)

    db.add(AuditLog(
        user_id=current_user.id, action="alert_resolved",
        entity_type="alert", entity_id=alert.id,
    ))
    db.commit()
    return alert


@router.get("/projects/{project_id}/drift")
def get_drift_stats(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Placeholder: returns mock drift statistics."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "project_id": project_id,
        "psi_7d": 0.062,
        "drift_alerts_open": 2,
        "features_drifting": ["merchant_risk_score", "model_output"],
        "weekly_psi": [0.021, 0.028, 0.019, 0.035, 0.024, 0.031, 0.048, 0.063, 0.044, 0.071, 0.078, 0.055],
    }
