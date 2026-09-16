from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..services.scorecard import generate_match_scorecard

router = APIRouter()

@router.get("/tournament/{tournament_id}", response_model=List[schemas.MatchResponse])
def get_tournament_matches(tournament_id: str, db: Session = Depends(get_db)):
    matches = db.query(models.Match).filter(models.Match.tournament_id == tournament_id).order_by(models.Match.match_number).all()
    return matches

@router.get("/{match_id}", response_model=schemas.MatchResponse)
def get_match(match_id: str, db: Session = Depends(get_db)):
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match

@router.get("/{match_id}/scorecard", response_model=schemas.MatchScorecardResponse)
def get_match_scorecard(match_id: str, db: Session = Depends(get_db)):
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    return generate_match_scorecard(db, match)

@router.post("/{match_id}/playing-xi")
def set_playing_xi(match_id: str, team_id: str, xi_data: schemas.PlayingXISchema, db: Session = Depends(get_db)):
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    if team_id == match.team1_id:
        match.team1_xi = xi_data.playing_xi
    elif team_id == match.team2_id:
        match.team2_xi = xi_data.playing_xi
    else:
        raise HTTPException(status_code=400, detail="Team is not part of this match")
        
    db.commit()
    return {"message": "Playing XI updated successfully"}

@router.post("/{match_id}/impact-player")
def set_impact_player(match_id: str, team_id: str, player_id: str, db: Session = Depends(get_db)):
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    if team_id == match.team1_id:
        match.team1_impact = player_id
    elif team_id == match.team2_id:
        match.team2_impact = player_id
    else:
        raise HTTPException(status_code=400, detail="Team is not part of this match")
        
    db.commit()
    return {"message": "Impact player updated successfully"}

@router.post("/{match_id}/toss")
def conduct_toss(match_id: str, db: Session = Depends(get_db)):
    import random
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    if match.toss_winner:
        raise HTTPException(status_code=400, detail="Toss already conducted")
        
    # Fair toss
    winner_id = random.choice([match.team1_id, match.team2_id])
    decision = random.choice(["BAT", "FIELD"])
    
    match.toss_winner = winner_id
    match.toss_decision = decision
    match.status = models.MatchStatus.LIVE
    
    db.commit()
    db.refresh(match)
    return {"toss_winner": winner_id, "toss_decision": decision}
