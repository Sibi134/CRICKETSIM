from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import random
import uuid

from .. import models, schemas
from ..database import get_db
from ..services import ai_rating

router = APIRouter()

@router.post("/import", response_model=schemas.TeamResponse, status_code=status.HTTP_201_CREATED)
def import_team(team_data: schemas.TeamImportRequest, db: Session = Depends(get_db)):
    # Check if team ID already exists
    existing_team = db.query(models.Team).filter(models.Team.id == team_data.team.id).first()
    if existing_team:
        raise HTTPException(status_code=400, detail="Team ID already exists")

    # Validate players
    if len(team_data.players) < 11:
        raise HTTPException(status_code=400, detail="Team must have at least 11 players")
        
    wk_count = sum(1 for p in team_data.players if "Wicketkeeper" in p.role)
    if wk_count < 1:
        raise HTTPException(status_code=400, detail="Team must have at least 1 Wicketkeeper")

    # Create Team
    db_team = models.Team(
        id=team_data.team.id,
        name=team_data.team.name,
        short_name=team_data.team.short_name,
        captain_id=team_data.team.captain_id,
        home_ground=team_data.team.home_ground,
        primary_color=team_data.team.primary_color,
        secondary_color=team_data.team.secondary_color
    )
    db.add(db_team)
    
    # Create Players
    for p_data in team_data.players:
        db_player = models.Player(
            id=p_data.id,
            team_id=db_team.id,
            name=p_data.name,
            nationality=p_data.nationality,
            is_overseas=p_data.is_overseas,
            role=p_data.role,
            batting_style=p_data.batting_style,
            bowling_style=p_data.bowling_style,
            availability=p_data.availability,
            availability_reason=p_data.availability_reason,
            ratings=p_data.ratings.dict()
        )
        db.add(db_player)
    
    try:
        db.commit()
        db.refresh(db_team)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    return db_team

@router.get("/", response_model=List[schemas.TeamResponse])
def get_teams(db: Session = Depends(get_db)):
    teams = db.query(models.Team).all()
    return teams

@router.get("/{team_id}", response_model=schemas.TeamResponse)
def get_team(team_id: str, db: Session = Depends(get_db)):
    db_team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")
    return db_team

import re

@router.post("/{team_id}/squad/paste")
def paste_squad(team_id: str, data: schemas.SquadPasteSchema, db: Session = Depends(get_db)):
    db_team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    names = data.player_names
    if not names:
        raise HTTPException(status_code=400, detail="No names provided")
        
    if data.replace:
        db.query(models.Player).filter(models.Player.team_id == team_id).delete()
        db_team.captain_id = None
        
    cleaned_names = []
    player_meta = {}
    
    for name_raw in names:
        name = name_raw.strip()
        if not name:
            continue
            
        # Remove leading numbers like "1.", "2 ", "12. "
        name = re.sub(r'^\d+[\.\)]?\s*', '', name)
        
        # Extract annotations
        is_captain = False
        is_vc = False
        
        if "(C)" in name.upper() or "— C" in name.upper() or "- C" in name.upper():
            is_captain = True
            name = re.sub(r'\(\s*[cC]\s*\)', '', name)
            name = re.sub(r'[—\-]\s*[cC]\b', '', name)
        if "(VC)" in name.upper() or "— VC" in name.upper() or "- VC" in name.upper():
            is_vc = True
            name = re.sub(r'\(\s*VC\s*\)', '', name, flags=re.IGNORECASE)
            name = re.sub(r'[—\-]\s*VC\b', '', name, flags=re.IGNORECASE)
        
        # We let the AI figure out the wicketkeeper role instead of relying purely on (WK), 
        # but we can clean it up from the name so the AI gets a clean name
        name = re.sub(r'\(\s*WK\s*\)', '', name, flags=re.IGNORECASE)
        name = re.sub(r'[—\-]\s*WK\b', '', name, flags=re.IGNORECASE)
            
        name = name.strip(" -—,")
        name_clean = name.replace("\u2060", "").strip()
        
        if name_clean:
            cleaned_names.append(name_clean)
            player_meta[name_clean] = {
                "is_captain": is_captain,
                "is_vc": is_vc,
                "original_name": name_clean
            }
            
    if not cleaned_names:
        raise HTTPException(status_code=400, detail="No valid names provided")
        
    # Call the AI to analyze all players at once
    try:
        ai_results = ai_rating.analyze_players(cleaned_names)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

    players_added = 0
    for name_clean in cleaned_names:
        meta = player_meta[name_clean]
        ai_data = ai_results.get(name_clean)
        
        if not ai_data:
            # Fallback if AI somehow misses the player
            role = "Unknown"
            primary_skill = None
            secondary_skill = None
            batting_style = None
            bowling_style = None
            ratings = None
            rating_status = "REVIEW_REQUIRED"
        else:
            role = ai_data.role
            primary_skill = ai_data.primarySkill
            secondary_skill = ai_data.secondarySkill
            batting_style = ai_data.battingStyle
            bowling_style = ai_data.bowlingStyle
            ratings = ai_data.ratings.dict()
            rating_status = "READY" if ai_rating.validate_ratings(ai_data) else "REVIEW_REQUIRED"
        
        db_player = models.Player(
            id=f"{team_id}_P_{uuid.uuid4().hex[:6].upper()}",
            team_id=team_id,
            name=meta["original_name"],
            nationality=None,
            is_overseas=False,
            role=role,
            primary_skill=primary_skill,
            secondary_skill=secondary_skill,
            batting_style=batting_style,
            bowling_style=bowling_style,
            availability=True,
            availability_reason="Available",
            is_captain=meta["is_captain"],
            is_vice_captain=meta["is_vc"],
            rating_status=rating_status,
            ratings=ratings
        )
        db.add(db_player)
        players_added += 1
        
        if meta["is_captain"]:
            db_team.captain_id = db_player.id
            
    db.commit()
    db.refresh(db_team)
    return db_team

@router.put("/{team_id}/players/{player_id}", response_model=schemas.PlayerSchema)
def update_player(team_id: str, player_id: str, player_data: schemas.PlayerUpdateSchema, db: Session = Depends(get_db)):
    db_player = db.query(models.Player).filter(models.Player.id == player_id, models.Player.team_id == team_id).first()
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found")
        
    if player_data.name is not None:
        db_player.name = player_data.name
    if player_data.nationality is not None:
        db_player.nationality = player_data.nationality
    if player_data.is_overseas is not None:
        db_player.is_overseas = player_data.is_overseas
    if player_data.role is not None:
        db_player.role = player_data.role
    if player_data.batting_style is not None:
        db_player.batting_style = player_data.batting_style
    if player_data.bowling_style is not None:
        db_player.bowling_style = player_data.bowling_style
    if player_data.availability is not None:
        db_player.availability = player_data.availability
    if player_data.availability_reason is not None:
        db_player.availability_reason = player_data.availability_reason
    
    if player_data.is_captain is not None:
        db_player.is_captain = player_data.is_captain
        if player_data.is_captain:
            team = db.query(models.Team).filter(models.Team.id == team_id).first()
            if team:
                team.captain_id = db_player.id
                
    if player_data.is_vice_captain is not None:
        db_player.is_vice_captain = player_data.is_vice_captain
        
    if player_data.ratings is not None:
        db_player.ratings = player_data.ratings.dict()
        db_player.rating_status = "READY"
        
    db.commit()
    db.refresh(db_player)
    return db_player

@router.post("/{team_id}/players", response_model=schemas.PlayerSchema, status_code=status.HTTP_201_CREATED)
def add_player(team_id: str, player_data: schemas.PlayerUpdateSchema, db: Session = Depends(get_db)):
    db_team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    db_player = models.Player(
        id=f"{team_id}_P_{uuid.uuid4().hex[:6].upper()}",
        team_id=team_id,
        name=player_data.name or "New Player",
        nationality=player_data.nationality,
        is_overseas=player_data.is_overseas or False,
        role=player_data.role or "Batter",
        batting_style=player_data.batting_style,
        bowling_style=player_data.bowling_style,
        availability=player_data.availability if player_data.availability is not None else True,
        availability_reason=player_data.availability_reason or "Available",
        is_captain=player_data.is_captain or False,
        is_vice_captain=player_data.is_vice_captain or False,
        rating_status="READY" if player_data.ratings else "UNRATED",
        ratings=player_data.ratings.dict() if player_data.ratings else None
    )
    
    db.add(db_player)
    
    if db_player.is_captain:
        db_team.captain_id = db_player.id
        
    db.commit()
    db.refresh(db_player)
    return db_player

@router.delete("/{team_id}/players/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(team_id: str, player_id: str, db: Session = Depends(get_db)):
    db_player = db.query(models.Player).filter(models.Player.id == player_id, models.Player.team_id == team_id).first()
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found")
        
    db.delete(db_player)
    db.commit()
    return None

@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_id: str, db: Session = Depends(get_db)):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    db.delete(team)
    db.commit()
    return None
