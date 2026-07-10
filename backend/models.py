from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Float, Integer, String, Text, DateTime, ForeignKey, JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="analyst")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    labels: Mapped[list["Label"]] = relationship(back_populates="analyst")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    model_type: Mapped[Optional[str]] = mapped_column(String(100))
    use_case: Mapped[Optional[str]] = mapped_column(String(255))
    data_source_config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    label_column: Mapped[Optional[str]] = mapped_column(String(255))
    time_column: Mapped[Optional[str]] = mapped_column(String(255))
    train_eval_split: Mapped[float] = mapped_column(Float, default=0.8)
    embargo_days: Mapped[int] = mapped_column(Integer, default=14)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    creator: Mapped[Optional["User"]] = relationship()
    datasets: Mapped[list["Dataset"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    runs: Mapped[list["Run"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    rules: Mapped[list["Rule"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    filepath: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    row_count: Mapped[Optional[int]] = mapped_column(Integer)
    column_count: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="datasets")
    versions: Mapped[list["DatasetVersion"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"
    __table_args__ = (UniqueConstraint("dataset_id", "version_num"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    version_num: Mapped[int] = mapped_column(Integer, nullable=False)
    row_count: Mapped[Optional[int]] = mapped_column(Integer)
    column_count: Mapped[Optional[int]] = mapped_column(Integer)
    positive_count: Mapped[Optional[int]] = mapped_column(Integer)
    negative_count: Mapped[Optional[int]] = mapped_column(Integer)
    positive_rate: Mapped[Optional[float]] = mapped_column(Float)
    profile_stats: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    dataset: Mapped["Dataset"] = relationship(back_populates="versions")


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    preset: Mapped[str] = mapped_column(String(50), default="performance")
    status: Mapped[str] = mapped_column(String(50), default="queued")
    feature_count: Mapped[Optional[int]] = mapped_column(Integer)
    feature_selection: Mapped[str] = mapped_column(String(50), default="auto")
    hyperparams: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    is_champion: Mapped[bool] = mapped_column(Boolean, default=False)
    is_challenger: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    project: Mapped["Project"] = relationship(back_populates="runs")
    creator: Mapped[Optional["User"]] = relationship()
    model_artifacts: Mapped[list["ModelArtifact"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class ModelArtifact(Base):
    __tablename__ = "model_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    filepath: Mapped[str] = mapped_column(String(500), nullable=False)
    model_format: Mapped[Optional[str]] = mapped_column(String(100))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run: Mapped["Run"] = relationship(back_populates="model_artifacts")


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    condition_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False)
    order_position: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    frequency_daily: Mapped[int] = mapped_column(Integer, default=0)
    last_fired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship(back_populates="rules")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    run_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("runs.id"))
    transaction_id: Mapped[Optional[str]] = mapped_column(String(255))
    score: Mapped[Optional[float]] = mapped_column(Float)
    decision: Mapped[Optional[str]] = mapped_column(String(50))
    threshold_used: Mapped[Optional[float]] = mapped_column(Float)
    rule_trace: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float)
    features_used: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="predictions")
    run: Mapped[Optional["Run"]] = relationship()
    labels: Mapped[list["Label"]] = relationship(back_populates="prediction", cascade="all, delete-orphan")


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prediction_id: Mapped[int] = mapped_column(Integer, ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False)
    analyst_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    prediction: Mapped["Prediction"] = relationship(back_populates="labels")
    analyst: Mapped["User"] = relationship(back_populates="labels")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    feature_name: Mapped[Optional[str]] = mapped_column(String(255))
    metric_value: Mapped[Optional[float]] = mapped_column(Float)
    threshold_value: Mapped[Optional[float]] = mapped_column(Float)
    message: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    project: Mapped["Project"] = relationship(back_populates="alerts")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    details: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[Optional["User"]] = relationship()
