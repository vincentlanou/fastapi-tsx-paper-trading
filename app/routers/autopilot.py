from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import autopilot_service

router = APIRouter(prefix="/api/autopilot", tags=["Autopilot Engine"])

@router.post("/run")
def trigger_autopilot_cycle(db: Session = Depends(get_db)):
    """
    Manually trigger the daily Autopilot rebalance cycle.
    This will evaluate exits, execute sells, scan the universe, and execute buys.
    """
    result = autopilot_service.run_autopilot(db)
    return result
