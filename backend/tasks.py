import time
import json
import logging
from datetime import datetime, timezone

from backend.celery_app import celery
from backend.database import SessionLocal
from backend.models import Run, DatasetVersion

logger = logging.getLogger(__name__)


@celery.task(bind=True, name="run_experiment")
def run_experiment(self, run_id: int):
    """Execute a model training run. Currently a placeholder that simulates training."""
    db = SessionLocal()
    try:
        run = db.query(Run).filter(Run.id == run_id).first()
        if not run:
            logger.error(f"Run {run_id} not found")
            return {"status": "error", "message": f"Run {run_id} not found"}

        # Mark as running
        run.status = "running"
        db.commit()
        logger.info(f"Run {run_id} started (preset={run.preset})")

        # Simulate training duration based on preset
        durations = {"speed": 5, "performance": 10, "quality": 15, "experimental": 20}
        duration = durations.get(run.preset, 10)
        time.sleep(duration)

        # Simulate metrics (placeholder — real ML training goes here)
        import random
        base_auc = 0.88 + random.uniform(0, 0.08)
        run.metrics = {
            "auc": round(base_auc, 4),
            "pr_auc": round(base_auc * 0.78, 4),
            "f1": round(base_auc * 0.91, 4),
            "precision": round(base_auc * 0.93, 4),
            "recall": round(base_auc * 0.89, 4),
            "log_loss": round(0.3 - base_auc * 0.15, 4),
            "ks_stat": round(base_auc * 0.77, 4),
        }
        run.feature_count = run.feature_count or 47
        run.duration_seconds = duration
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(f"Run {run_id} completed: AUC={run.metrics['auc']}")

        # Publish notification via Redis
        try:
            import redis as redis_lib
            from backend.config import settings
            r = redis_lib.from_url(settings.redis_url)
            r.publish("job_updates", json.dumps({
                "type": "run_completed",
                "run_id": run_id,
                "project_id": run.project_id,
                "metrics": run.metrics,
            }))
        except Exception:
            pass  # Non-critical

        return {"status": "completed", "run_id": run_id, "auc": run.metrics["auc"]}

    except Exception as e:
        logger.exception(f"Run {run_id} failed: {e}")
        run = db.query(Run).filter(Run.id == run_id).first()
        if run:
            run.status = "failed"
            db.commit()
        return {"status": "failed", "run_id": run_id, "error": str(e)}
    finally:
        db.close()


@celery.task(bind=True, name="profile_dataset")
def profile_dataset(self, dataset_id: int, version_id: int):
    """Profile a dataset version. Currently a placeholder."""
    db = SessionLocal()
    try:
        version = db.query(DatasetVersion).filter(DatasetVersion.id == version_id).first()
        if not version:
            return {"status": "error", "message": "Version not found"}

        # Placeholder: in reality, read the file and compute stats
        time.sleep(3)

        version.profile_stats = {
            "profiled_at": datetime.now(timezone.utc).isoformat(),
            "status": "complete",
            "columns": [],  # Would contain per-column stats
        }
        db.commit()
        logger.info(f"Dataset version {version_id} profiled")
        return {"status": "completed", "version_id": version_id}
    except Exception as e:
        logger.exception(f"Profile failed for version {version_id}: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery.task(bind=True, name="run_test_harness")
def run_test_harness(self, project_id: int, rule_ids: list = None):
    """Backtest rules against historical data. Currently a placeholder."""
    logger.info(f"Test harness started for project {project_id}, rules={rule_ids}")
    time.sleep(5)
    return {
        "status": "completed",
        "project_id": project_id,
        "cases_tested": 0,
        "accuracy": 0.0,
    }
