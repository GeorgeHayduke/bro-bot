from fastapi import APIRouter

from backend.api import auth, projects, runs, datasets, rules, predictions, labels, monitoring, events

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(runs.router)
api_router.include_router(datasets.router)
api_router.include_router(rules.router)
api_router.include_router(predictions.router)
api_router.include_router(labels.router)
api_router.include_router(monitoring.router)
api_router.include_router(events.router)
