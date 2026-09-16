from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import itertools
import random
from datetime import datetime, timedelta

from .. import models, schemas
from ..database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.TournamentResponse, status_code=status.HTTP_201_CREATED)
def create_tournament(tournament_data: schemas.TournamentCreate, db: Session = Depends(get_db)):
    db_tournament = models.Tournament(
        id=f"TOURNAMENT_{uuid.uuid4().hex[:8].upper()}",
        name=tournament_data.name,
        overs_per_innings=tournament_data.overs_per_innings,
        points_win=tournament_data.points_win,
        points_tie=tournament_data.points_tie,
        points_nr=tournament_data.points_nr,
        max_overseas_players=tournament_data.max_overseas_players,
        impact_player_enabled=tournament_data.impact_player_enabled,
        status=models.TournamentStatus.SETUP
    )
    db.add(db_tournament)
    db.commit()
    db.refresh(db_tournament)
    return db_tournament

@router.get("/", response_model=List[schemas.TournamentResponse])
def get_tournaments(db: Session = Depends(get_db)):
    return db.query(models.Tournament).all()

@router.get("/{tournament_id}", response_model=schemas.TournamentResponse)
def get_tournament(tournament_id: str, db: Session = Depends(get_db)):
    tournament = db.query(models.Tournament).filter(models.Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tournament

@router.delete("/{tournament_id}")
def delete_tournament(tournament_id: str, db: Session = Depends(get_db)):
    tournament = db.query(models.Tournament).filter(models.Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
        
    db.delete(tournament)
    db.commit()
    return {"message": "Tournament deleted successfully"}

@router.post("/{tournament_id}/schedule/generate")
def generate_schedule(tournament_id: str, db: Session = Depends(get_db)):
    tournament = db.query(models.Tournament).filter(models.Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
        
    if tournament.status != models.TournamentStatus.SETUP:
        raise HTTPException(status_code=400, detail="Schedule can only be generated in SETUP status")

    teams = db.query(models.Team).all()
    if len(teams) < 2:
        raise HTTPException(status_code=400, detail="At least 2 teams required to generate schedule")

    # Round Robin Generation
    team_ids = [t.id for t in teams]
    random.shuffle(team_ids)
    
    matchups = list(itertools.combinations(team_ids, 2))
    random.shuffle(matchups) # Randomize match order
    
    start_date = datetime.utcnow() + timedelta(days=1)
    
    matches_created = []
    for i, (t1, t2) in enumerate(matchups):
        match_date = start_date + timedelta(days=i)
        db_match = models.Match(
            id=f"MATCH_{uuid.uuid4().hex[:8].upper()}",
            tournament_id=tournament.id,
            match_number=i + 1,
            team1_id=t1,
            team2_id=t2,
            venue="Tournament Venue", # Can be mapped to home ground later
            scheduled_date=match_date,
            status=models.MatchStatus.UPCOMING
        )
        db.add(db_match)
        matches_created.append(db_match)
    
    tournament.status = models.TournamentStatus.LEAGUE
    db.commit()
    
    return {"message": f"Generated {len(matches_created)} matches successfully", "matches": len(matches_created)}

from ..services.tournament_logic import calculate_standings
from ..services.stats_service import generate_tournament_stats

@router.get("/{tournament_id}/standings")
def get_standings(tournament_id: str, db: Session = Depends(get_db)):
    tournament = db.query(models.Tournament).filter(models.Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return calculate_standings(db, tournament_id)

@router.get("/{tournament_id}/stats", response_model=schemas.TournamentStatsResponse)
def get_stats(tournament_id: str, db: Session = Depends(get_db)):
    tournament = db.query(models.Tournament).filter(models.Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return generate_tournament_stats(db, tournament_id)

@router.post("/{tournament_id}/playoffs/progress")
def progress_playoffs(tournament_id: str, db: Session = Depends(get_db)):
    tournament = db.query(models.Tournament).filter(models.Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
        
    # Check if league stage is done (all UPCOMING/LIVE matches are completed?)
    active_matches = db.query(models.Match).filter(
        models.Match.tournament_id == tournament_id,
        models.Match.status != models.MatchStatus.COMPLETED
    ).count()
    
    if active_matches > 0:
        raise HTTPException(status_code=400, detail="Cannot progress, there are unfinished matches")
        
    # Depending on current tournament status, progress
    standings = calculate_standings(db, tournament_id)
    if len(standings) < 4:
        raise HTTPException(status_code=400, detail="Not enough teams for playoffs")
        
    top_4 = [s["team_id"] for s in standings[:4]]
    
    import uuid
    from datetime import datetime, timedelta
    
    # If tournament is still in LEAGUE, generate Q1 and Eliminator
    if tournament.status == models.TournamentStatus.LEAGUE:
        tournament.status = models.TournamentStatus.PLAYOFFS
        
        # Qualifier 1: Rank 1 vs Rank 2
        m_q1 = models.Match(
            id=f"MATCH_{uuid.uuid4().hex[:8].upper()}",
            tournament_id=tournament.id,
            match_number=101, # Hack to denote playoffs
            team1_id=top_4[0],
            team2_id=top_4[1],
            venue="Qualifier 1",
            scheduled_date=datetime.utcnow(),
            status=models.MatchStatus.UPCOMING
        )
        # Eliminator: Rank 3 vs Rank 4
        m_elim = models.Match(
            id=f"MATCH_{uuid.uuid4().hex[:8].upper()}",
            tournament_id=tournament.id,
            match_number=102,
            team1_id=top_4[2],
            team2_id=top_4[3],
            venue="Eliminator",
            scheduled_date=datetime.utcnow() + timedelta(days=1),
            status=models.MatchStatus.UPCOMING
        )
        db.add(m_q1)
        db.add(m_elim)
        db.commit()
        return {"message": "Qualifier 1 and Eliminator scheduled."}
        
    # Logic for Q2 and Final would go here by checking match_number=101, 102 results
    return {"message": "Playoffs progress logic for later stages."}
