from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..services.simulation.engine import MatchSimulationEngine

router = APIRouter()

@router.post("/{match_id}/simulate/{overs}")
def simulate_overs(match_id: str, overs: str, db: Session = Depends(get_db)):
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    if match.status == models.MatchStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Match is already completed")
        
    num_overs = 1
    if overs == "1-over":
        num_overs = 1
    elif overs == "5-overs":
        num_overs = 5
    elif overs == "10-overs":
        num_overs = 10
    elif overs == "innings":
        num_overs = 20 # Assuming max
    else:
        raise HTTPException(status_code=400, detail="Invalid simulation period")
        
    engine = MatchSimulationEngine(db, match)
    engine.simulate_overs(num_overs)
    
    return {"message": f"Simulated {num_overs} overs successfully", "status": match.status}
