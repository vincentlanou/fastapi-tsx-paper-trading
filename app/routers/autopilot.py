from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db, SessionLocal
from app.services import autopilot_service

router = APIRouter(prefix="/api/autopilot", tags=["Autopilot Engine"])

def run_autopilot_task():
    db = SessionLocal()
    try:
        autopilot_service.run_autopilot(db)
    finally:
        db.close()

@router.post("/run")
def trigger_autopilot_cycle(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Triggers the daily Autopilot rebalance cycle asynchronously.
    Returns immediately so cron services do not time out.
    """
    background_tasks.add_task(run_autopilot_task)
    return {
        "status": "started",
        "message": "Autopilot cycle triggered in background. Telegram notification will be sent upon completion."
    }
