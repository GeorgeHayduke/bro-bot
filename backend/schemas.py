from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ── Auth ──

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── User ──

class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: str = "analyst"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Project ──

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    model_type: Optional[str] = None
    use_case: Optional[str] = None
    data_source_config: Optional[dict] = None
    label_column: Optional[str] = None
    time_column: Optional[str] = None
    train_eval_split: float = 0.8
    embargo_days: int = 14

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    model_type: Optional[str] = None
    use_case: Optional[str] = None
    data_source_config: Optional[dict] = None
    label_column: Optional[str] = None
    time_column: Optional[str] = None
    train_eval_split: Optional[float] = None
    embargo_days: Optional[int] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    status: str
    model_type: Optional[str] = None
    use_case: Optional[str] = None
    data_source_config: Optional[dict] = None
    label_column: Optional[str] = None
    time_column: Optional[str] = None
    train_eval_split: float
    embargo_days: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class ProjectSummary(ProjectResponse):
    run_count: int = 0
    champion_auc: Optional[float] = None
    latest_run_name: Optional[str] = None


# ── Dataset ──

class DatasetCreate(BaseModel):
    name: Optional[str] = None
    source_type: str
    filepath: Optional[str] = None

class DatasetResponse(BaseModel):
    id: int
    project_id: int
    name: Optional[str] = None
    source_type: Optional[str] = None
    filepath: Optional[str] = None
    file_size: Optional[int] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Dataset Version ──

class DatasetVersionResponse(BaseModel):
    id: int
    dataset_id: int
    version_num: int
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    positive_count: Optional[int] = None
    negative_count: Optional[int] = None
    positive_rate: Optional[float] = None
    profile_stats: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Run ──

class RunCreate(BaseModel):
    name: Optional[str] = None
    preset: str = "performance"
    feature_selection: str = "auto"
    time_limit_seconds: Optional[int] = 3600

class RunUpdate(BaseModel):
    status: Optional[str] = None
    is_champion: Optional[bool] = None
    is_challenger: Optional[bool] = None

class RunResponse(BaseModel):
    id: int
    project_id: int
    name: Optional[str] = None
    preset: str
    status: str
    feature_count: Optional[int] = None
    feature_selection: str
    hyperparams: Optional[dict] = None
    metrics: Optional[dict] = None
    duration_seconds: Optional[float] = None
    is_champion: bool
    is_challenger: bool
    created_by: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Model Artifact ──

class ModelArtifactResponse(BaseModel):
    id: int
    run_id: int
    filepath: str
    model_format: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Rule ──

class RuleCreate(BaseModel):
    name: str
    condition_json: dict
    outcome: str
    order_position: Optional[int] = None

class RuleUpdate(BaseModel):
    name: Optional[str] = None
    condition_json: Optional[dict] = None
    outcome: Optional[str] = None
    order_position: Optional[int] = None
    is_active: Optional[bool] = None

class RuleResponse(BaseModel):
    id: int
    project_id: int
    name: str
    condition_json: dict
    outcome: str
    order_position: int
    is_active: bool
    frequency_daily: int
    last_fired_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class RuleReorderItem(BaseModel):
    rule_id: int
    order_position: int

class RuleReorderRequest(BaseModel):
    rules: list[RuleReorderItem]


# ── Prediction ──

class PredictionCreate(BaseModel):
    transaction_id: Optional[str] = None
    score: Optional[float] = None
    decision: Optional[str] = None
    threshold_used: Optional[float] = None
    rule_trace: Optional[list] = None
    latency_ms: Optional[float] = None
    features_used: Optional[dict] = None
    run_id: Optional[int] = None

class PredictionResponse(BaseModel):
    id: int
    project_id: int
    run_id: Optional[int] = None
    transaction_id: Optional[str] = None
    score: Optional[float] = None
    decision: Optional[str] = None
    threshold_used: Optional[float] = None
    rule_trace: Optional[list] = None
    latency_ms: Optional[float] = None
    features_used: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Label ──

class LabelCreate(BaseModel):
    label: str  # fraud, legit, skip

class LabelResponse(BaseModel):
    id: int
    prediction_id: int
    analyst_id: int
    label: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Alert ──

class AlertResponse(BaseModel):
    id: int
    project_id: int
    alert_type: str
    severity: str
    feature_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    message: Optional[str] = None
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class AlertUpdate(BaseModel):
    status: Optional[str] = None


# ── Audit Log ──

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    details: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Pagination ──

class PaginatedResponse(BaseModel):
    items: list
    total: int
    skip: int
    limit: int
