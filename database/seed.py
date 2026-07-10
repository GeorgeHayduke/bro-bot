"""
Seed script — populates the database with sample data matching the HTML prototype.

Usage:
    docker-compose exec app python -m database.seed
"""
import sys
import os

# Ensure backend is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone, timedelta
from backend.database import SessionLocal, engine
from backend.models import (
    Base, User, Project, Dataset, DatasetVersion, Run,
    Rule, Prediction, Label, Alert, AuditLog,
)
from backend.auth import hash_password


def seed():
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(User).first():
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        # ── Users ──
        admin = User(
            email="admin@jha.com", name="Admin User",
            hashed_password=hash_password("admin123"), role="admin",
        )
        ds_user = User(
            email="sarah.chen@jha.com", name="Sarah Chen",
            hashed_password=hash_password("password"), role="data_scientist",
        )
        analyst = User(
            email="mike.reynolds@jha.com", name="Mike Reynolds",
            hashed_password=hash_password("password"), role="analyst",
        )
        db.add_all([admin, ds_user, analyst])
        db.flush()
        print(f"  Users: {admin.id}, {ds_user.id}, {analyst.id}")

        # ── Project 1: Payments Fraud Detection ──
        fraud_project = Project(
            name="Payments Fraud Detection",
            description="Real-time payment fraud scoring for card-not-present transactions",
            status="deployed",
            model_type="binary_classification",
            use_case="Risk / Fraud",
            label_column="is_fraud",
            time_column="txn_timestamp",
            train_eval_split=0.8,
            embargo_days=14,
            created_by=ds_user.id,
            data_source_config={
                "connector": "bigquery",
                "project": "jha-prod",
                "dataset": "ml_features",
                "table": "txn_features_v4",
            },
        )
        db.add(fraud_project)
        db.flush()

        # Fraud dataset
        fraud_ds = Dataset(
            project_id=fraud_project.id,
            name="prod.txn_features_v4",
            source_type="bigquery",
            filepath="jha-prod.ml_features.txn_features_v4",
            row_count=4800000,
            column_count=84,
        )
        db.add(fraud_ds)
        db.flush()

        fraud_dsv = DatasetVersion(
            dataset_id=fraud_ds.id, version_num=1,
            row_count=19000, column_count=47,
            positive_count=532, negative_count=18468,
            positive_rate=0.028,
            profile_stats={"status": "complete", "profiled_at": "2026-03-15T10:00:00Z"},
        )
        db.add(fraud_dsv)

        # Fraud runs (matching prototype exactly)
        fraud_runs_data = [
            {"name": "run-005", "preset": "quality", "features": 47,
             "metrics": {"auc": 0.9287, "pr_auc": 0.698, "f1": 0.824, "precision": 0.838, "recall": 0.811, "log_loss": 0.131, "ks_stat": 0.6992},
             "duration": 7080, "date": datetime(2026, 3, 8, 8, 55, tzinfo=timezone.utc)},
            {"name": "run-006", "preset": "speed", "features": 31,
             "metrics": {"auc": 0.9198, "pr_auc": 0.681, "f1": 0.811, "precision": 0.826, "recall": 0.797, "log_loss": 0.142, "ks_stat": 0.6823},
             "duration": 720, "date": datetime(2026, 3, 12, 11, 20, tzinfo=timezone.utc)},
            {"name": "run-007", "preset": "quality", "features": 52,
             "metrics": {"auc": 0.9350, "pr_auc": 0.710, "f1": 0.832, "precision": 0.847, "recall": 0.818, "log_loss": 0.126, "ks_stat": 0.7105},
             "duration": 7260, "date": datetime(2026, 3, 15, 16, 44, tzinfo=timezone.utc)},
            {"name": "run-008", "preset": "performance", "features": 47,
             "metrics": {"auc": 0.9381, "pr_auc": 0.714, "f1": 0.838, "precision": 0.851, "recall": 0.826, "log_loss": 0.122, "ks_stat": 0.7148},
             "duration": 2280, "date": datetime(2026, 3, 18, 9, 15, tzinfo=timezone.utc)},
            {"name": "run-009", "preset": "quality", "features": 47,
             "metrics": {"auc": 0.9412, "pr_auc": 0.721, "f1": 0.847, "precision": 0.863, "recall": 0.832, "log_loss": 0.118, "ks_stat": 0.7213},
             "duration": 8040, "date": datetime(2026, 3, 20, 14, 32, tzinfo=timezone.utc)},
        ]

        fraud_runs = []
        for rd in fraud_runs_data:
            run = Run(
                project_id=fraud_project.id,
                name=rd["name"],
                preset=rd["preset"],
                status="completed",
                feature_count=rd["features"],
                metrics=rd["metrics"],
                duration_seconds=rd["duration"],
                created_by=ds_user.id,
                created_at=rd["date"],
                completed_at=rd["date"] + timedelta(seconds=rd["duration"]),
            )
            fraud_runs.append(run)
        # Set champion and challenger
        fraud_runs[-1].is_champion = True   # run-009
        fraud_runs[-2].is_challenger = True  # run-008
        db.add_all(fraud_runs)
        db.flush()

        # Fraud rules (matching prototype)
        fraud_rules = [
            Rule(project_id=fraud_project.id, name="Low-risk auto-approve",
                 condition_json={"conditions": [{"field": "fraud_score", "op": "<", "value": 0.40}]},
                 outcome="APPROVE", order_position=1, frequency_daily=4821),
            Rule(project_id=fraud_project.id, name="Crypto high-amount block",
                 condition_json={"conditions": [
                     {"field": "fraud_score", "op": ">", "value": 0.55},
                     {"field": "merchant_category", "op": "=", "value": "crypto"},
                     {"field": "amount", "op": ">", "value": 2000},
                 ]},
                 outcome="BLOCK", order_position=2, frequency_daily=38),
            Rule(project_id=fraud_project.id, name="Velocity spike block",
                 condition_json={"conditions": [
                     {"field": "velocity_24h", "op": ">", "value": 12},
                     {"field": "fraud_score", "op": ">", "value": 0.50},
                 ]},
                 outcome="BLOCK", order_position=3, frequency_daily=22),
            Rule(project_id=fraud_project.id, name="Moderate risk review",
                 condition_json={"conditions": [
                     {"field": "fraud_score", "op": ">=", "value": 0.55},
                     {"field": "fraud_score", "op": "<", "value": 0.80},
                 ]},
                 outcome="REVIEW", order_position=4, frequency_daily=312),
            Rule(project_id=fraud_project.id, name="High-risk block",
                 condition_json={"conditions": [
                     {"field": "fraud_score", "op": ">=", "value": 0.80},
                     {"field": "amount", "op": ">", "value": 500},
                 ]},
                 outcome="BLOCK", order_position=5, frequency_daily=91),
            Rule(project_id=fraud_project.id, name="Very high-risk escalate",
                 condition_json={"conditions": [{"field": "fraud_score", "op": ">=", "value": 0.92}]},
                 outcome="ESCALATE", order_position=6, frequency_daily=18),
        ]
        db.add_all(fraud_rules)

        # Sample fraud predictions
        fraud_preds_data = [
            {"txn": "TXN-88291", "score": 0.923, "decision": "BLOCKED", "latency": 12},
            {"txn": "TXN-88292", "score": 0.871, "decision": "BLOCKED", "latency": 14},
            {"txn": "TXN-88293", "score": 0.744, "decision": "REVIEW", "latency": 11},
            {"txn": "TXN-88294", "score": 0.312, "decision": "APPROVE", "latency": 9},
            {"txn": "TXN-88295", "score": 0.651, "decision": "REVIEW", "latency": 15},
            {"txn": "TXN-88296", "score": 0.089, "decision": "APPROVE", "latency": 8},
            {"txn": "TXN-88297", "score": 0.952, "decision": "ESCALATE", "latency": 13},
            {"txn": "TXN-88298", "score": 0.567, "decision": "REVIEW", "latency": 11},
        ]
        champion_run = fraud_runs[-1]
        fraud_predictions = []
        for pd_data in fraud_preds_data:
            pred = Prediction(
                project_id=fraud_project.id,
                run_id=champion_run.id,
                transaction_id=pd_data["txn"],
                score=pd_data["score"],
                decision=pd_data["decision"],
                threshold_used=0.70,
                latency_ms=pd_data["latency"],
            )
            fraud_predictions.append(pred)
        db.add_all(fraud_predictions)
        db.flush()

        # Sample labels
        db.add_all([
            Label(prediction_id=fraud_predictions[0].id, analyst_id=analyst.id, label="fraud"),
            Label(prediction_id=fraud_predictions[1].id, analyst_id=analyst.id, label="fraud"),
            Label(prediction_id=fraud_predictions[2].id, analyst_id=analyst.id, label="legit"),
            Label(prediction_id=fraud_predictions[3].id, analyst_id=analyst.id, label="legit"),
        ])

        # Fraud alerts
        db.add_all([
            Alert(
                project_id=fraud_project.id, alert_type="drift", severity="high",
                feature_name="merchant_risk_score", metric_value=0.071,
                threshold_value=0.05, message="PSI crossed warning threshold",
                status="open",
                created_at=datetime(2026, 3, 24, 11, 2, tzinfo=timezone.utc),
            ),
            Alert(
                project_id=fraud_project.id, alert_type="drift", severity="med",
                feature_name="model_output", metric_value=0.055,
                threshold_value=0.05, message="Score distribution drift detected",
                status="acknowledged",
                created_at=datetime(2026, 3, 23, 8, 15, tzinfo=timezone.utc),
            ),
            Alert(
                project_id=fraud_project.id, alert_type="drift", severity="low",
                feature_name="txn_velocity_1h", metric_value=0.041,
                threshold_value=0.05, message="Minor velocity distribution shift",
                status="resolved",
                created_at=datetime(2026, 3, 20, 14, 30, tzinfo=timezone.utc),
                resolved_at=datetime(2026, 3, 21, 9, 0, tzinfo=timezone.utc),
            ),
        ])

        # ── Project 2: Loan Early Default ──
        loan_project = Project(
            name="Loan Early Default",
            description="Predict early loan default within 90 days of origination",
            status="experimenting",
            model_type="binary_classification",
            use_case="Default Prediction",
            label_column="early_default",
            time_column="origination_date",
            train_eval_split=0.8,
            embargo_days=14,
            created_by=ds_user.id,
            data_source_config={
                "connector": "s3",
                "bucket": "jha-data",
                "prefix": "loan-features/",
                "format": "parquet",
            },
        )
        db.add(loan_project)
        db.flush()

        # Loan dataset
        loan_ds = Dataset(
            project_id=loan_project.id,
            name="s3://jha-data/loan-features/",
            source_type="s3",
            filepath="s3://jha-data/loan-features/",
            row_count=1200000,
            column_count=62,
        )
        db.add(loan_ds)
        db.flush()

        loan_dsv = DatasetVersion(
            dataset_id=loan_ds.id, version_num=1,
            row_count=12000, column_count=38,
            positive_count=480, negative_count=11520,
            positive_rate=0.04,
            profile_stats={"status": "complete"},
        )
        db.add(loan_dsv)

        # Loan runs
        loan_runs_data = [
            {"name": "run-001", "preset": "speed", "features": 38,
             "metrics": {"auc": 0.8521, "pr_auc": 0.541, "f1": 0.712, "precision": 0.734, "recall": 0.691, "log_loss": 0.268, "ks_stat": 0.5912},
             "duration": 480, "date": datetime(2026, 3, 5, 10, 0, tzinfo=timezone.utc)},
            {"name": "run-002", "preset": "performance", "features": 38,
             "metrics": {"auc": 0.8714, "pr_auc": 0.568, "f1": 0.731, "precision": 0.752, "recall": 0.711, "log_loss": 0.249, "ks_stat": 0.6124},
             "duration": 1440, "date": datetime(2026, 3, 8, 14, 30, tzinfo=timezone.utc)},
            {"name": "run-003", "preset": "quality", "features": 42,
             "metrics": {"auc": 0.8801, "pr_auc": 0.589, "f1": 0.746, "precision": 0.768, "recall": 0.725, "log_loss": 0.238, "ks_stat": 0.6287},
             "duration": 5400, "date": datetime(2026, 3, 12, 9, 0, tzinfo=timezone.utc)},
            {"name": "run-004", "preset": "quality", "features": 38,
             "metrics": {"auc": 0.8872, "pr_auc": 0.623, "f1": 0.763, "precision": 0.989, "recall": 0.692, "log_loss": 0.214, "ks_stat": 0.6541},
             "duration": 6000, "date": datetime(2026, 3, 15, 11, 0, tzinfo=timezone.utc)},
            {"name": "run-005", "preset": "performance", "features": 38,
             "metrics": {"auc": 0.9021, "pr_auc": 0.641, "f1": 0.778, "precision": 0.801, "recall": 0.756, "log_loss": 0.201, "ks_stat": 0.6712},
             "duration": 1800, "date": datetime(2026, 3, 18, 16, 0, tzinfo=timezone.utc)},
            {"name": "run-006", "preset": "experimental", "features": 45,
             "metrics": {"auc": 0.9187, "pr_auc": 0.658, "f1": 0.791, "precision": 0.812, "recall": 0.771, "log_loss": 0.192, "ks_stat": 0.6891},
             "duration": 7200, "date": datetime(2026, 3, 22, 10, 0, tzinfo=timezone.utc)},
            {"name": "run-007", "preset": "quality", "features": 42,
             "metrics": {"auc": 0.9420, "pr_auc": 0.681, "f1": 0.812, "precision": 0.834, "recall": 0.791, "log_loss": 0.178, "ks_stat": 0.7102},
             "duration": 6600, "date": datetime(2026, 3, 25, 14, 0, tzinfo=timezone.utc)},
        ]

        loan_runs = []
        for rd in loan_runs_data:
            run = Run(
                project_id=loan_project.id,
                name=rd["name"],
                preset=rd["preset"],
                status="completed",
                feature_count=rd["features"],
                metrics=rd["metrics"],
                duration_seconds=rd["duration"],
                created_by=ds_user.id,
                created_at=rd["date"],
                completed_at=rd["date"] + timedelta(seconds=rd["duration"]),
            )
            loan_runs.append(run)
        loan_runs[-1].is_champion = True  # run-007
        db.add_all(loan_runs)

        # Audit log for seeding
        db.add(AuditLog(
            user_id=admin.id, action="database_seeded",
            entity_type="system", entity_id=0,
            details={"projects": 2, "users": 3},
        ))

        db.commit()
        print("Seed complete!")
        print(f"  Projects: {fraud_project.id} (Fraud), {loan_project.id} (Loan)")
        print(f"  Fraud runs: {len(fraud_runs)}, Loan runs: {len(loan_runs)}")
        print(f"  Rules: {len(fraud_rules)}")
        print(f"  Predictions: {len(fraud_predictions)}")
        print(f"  Alerts: 3")
        print()
        print("Login credentials:")
        print("  admin@jha.com / admin123 (admin)")
        print("  sarah.chen@jha.com / password (data_scientist)")
        print("  mike.reynolds@jha.com / password (analyst)")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
