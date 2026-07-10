from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Rule, Project, AuditLog, User
from backend.schemas import RuleCreate, RuleUpdate, RuleResponse, RuleReorderRequest
from backend.auth import get_current_user, require_role

router = APIRouter(prefix="/projects/{project_id}/rules", tags=["rules"])


def _get_project(project_id: int, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_model=list[RuleResponse])
def list_rules(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_project(project_id, db)
    return db.query(Rule).filter(Rule.project_id == project_id).order_by(Rule.order_position).all()


@router.post("", response_model=RuleResponse, status_code=201)
def create_rule(
    project_id: int,
    payload: RuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "data_scientist")),
):
    _get_project(project_id, db)

    if payload.outcome not in ("APPROVE", "REVIEW", "BLOCK", "ESCALATE"):
        raise HTTPException(status_code=400, detail="Invalid outcome")

    # Auto-assign order if not provided
    if payload.order_position is None:
        max_order = db.query(Rule).filter(Rule.project_id == project_id).count()
        order = max_order + 1
    else:
        order = payload.order_position

    rule = Rule(
        project_id=project_id,
        name=payload.name,
        condition_json=payload.condition_json,
        outcome=payload.outcome,
        order_position=order,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    db.add(AuditLog(
        user_id=current_user.id, action="rule_created",
        entity_type="rule", entity_id=rule.id,
        details={"name": rule.name, "outcome": rule.outcome},
    ))
    db.commit()
    return rule


@router.put("/{rule_id}", response_model=RuleResponse)
def update_rule(
    project_id: int,
    rule_id: int,
    payload: RuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "data_scientist")),
):
    rule = db.query(Rule).filter(Rule.id == rule_id, Rule.project_id == project_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "outcome" in update_data and update_data["outcome"] not in ("APPROVE", "REVIEW", "BLOCK", "ESCALATE"):
        raise HTTPException(status_code=400, detail="Invalid outcome")

    for key, value in update_data.items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)

    db.add(AuditLog(
        user_id=current_user.id, action="rule_updated",
        entity_type="rule", entity_id=rule.id,
        details=update_data,
    ))
    db.commit()
    return rule


@router.delete("/{rule_id}", status_code=204)
def delete_rule(
    project_id: int,
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "data_scientist")),
):
    rule = db.query(Rule).filter(Rule.id == rule_id, Rule.project_id == project_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.add(AuditLog(
        user_id=current_user.id, action="rule_deleted",
        entity_type="rule", entity_id=rule.id,
        details={"name": rule.name},
    ))
    db.delete(rule)
    db.commit()


@router.put("/reorder", response_model=list[RuleResponse])
def reorder_rules(
    project_id: int,
    payload: RuleReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "data_scientist")),
):
    _get_project(project_id, db)

    for item in payload.rules:
        rule = db.query(Rule).filter(Rule.id == item.rule_id, Rule.project_id == project_id).first()
        if rule:
            rule.order_position = item.order_position
    db.commit()

    db.add(AuditLog(
        user_id=current_user.id, action="rules_reordered",
        entity_type="project", entity_id=project_id,
    ))
    db.commit()
    return db.query(Rule).filter(Rule.project_id == project_id).order_by(Rule.order_position).all()
