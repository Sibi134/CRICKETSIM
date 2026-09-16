from sqlalchemy import Column, String, Integer, Boolean, Float, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
import enum
from .database import Base
from datetime import datetime

class MatchStatus(str, enum.Enum):
    UPCOMING = "UPCOMING"
    LIVE = "LIVE"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"

class TournamentStatus(str, enum.Enum):
    SETUP = "SETUP"
    LEAGUE = "LEAGUE"
    PLAYOFFS = "PLAYOFFS"
    COMPLETED = "COMPLETED"

class Team(Base):
    __tablename__ = "teams"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    short_name = Column(String)
    captain_id = Column(String, nullable=True)
    home_ground = Column(String, nullable=True)
    primary_color = Column(String, default="#000000")
    secondary_color = Column(String, default="#ffffff")

    players = relationship("Player", back_populates="team", cascade="all, delete-orphan")

class Player(Base):
    __tablename__ = "players"
    id = Column(String, primary_key=True, index=True)
    team_id = Column(String, ForeignKey("teams.id"))
    name = Column(String, index=True)
    nationality = Column(String, nullable=True)
    is_overseas = Column(Boolean, default=False)
    role = Column(String, nullable=True)
    batting_style = Column(String, nullable=True)
    bowling_style = Column(String, nullable=True)
    availability = Column(Boolean, default=True)
    availability_reason = Column(String, default="Available")
    
    is_captain = Column(Boolean, default=False)
    is_vice_captain = Column(Boolean, default=False)
    rating_status = Column(String, default="UNRATED")
    
    primary_skill = Column(String, nullable=True) # batting, bowling, all_round, wicketkeeping
    secondary_skill = Column(String, nullable=True)
    
    # JSON for flexibility, or we could use individual columns
    ratings = Column(JSON, nullable=True)

    team = relationship("Team", back_populates="players")

class Tournament(Base):
    __tablename__ = "tournaments"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    status = Column(String, default=TournamentStatus.SETUP)
    overs_per_innings = Column(Integer, default=20)
    points_win = Column(Integer, default=2)
    points_tie = Column(Integer, default=1)
    points_nr = Column(Integer, default=1)
    max_overseas_players = Column(Integer, default=4)
    impact_player_enabled = Column(Boolean, default=True)
    
    matches = relationship("Match", back_populates="tournament", cascade="all, delete-orphan")

class Match(Base):
    __tablename__ = "matches"
    id = Column(String, primary_key=True, index=True)
    tournament_id = Column(String, ForeignKey("tournaments.id"))
    match_number = Column(Integer) # 1 to N, Playoffs 101, etc.
    team1_id = Column(String, ForeignKey("teams.id"))
    team2_id = Column(String, ForeignKey("teams.id"))
    venue = Column(String)
    scheduled_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default=MatchStatus.UPCOMING)
    toss_winner = Column(String, ForeignKey("teams.id"), nullable=True)
    toss_decision = Column(String, nullable=True) # BAT or FIELD
    pitch_type = Column(String, default="BALANCED")
    simulation_seed = Column(Integer, nullable=True)
    simulation_version = Column(String, default="1.0.0")
    winner = Column(String, ForeignKey("teams.id"), nullable=True)
    result_type = Column(String, nullable=True)
    player_of_match = Column(String, ForeignKey("players.id"), nullable=True)
    
    # Store lineups as JSON arrays of player IDs
    team1_xi = Column(JSON, nullable=True)
    team2_xi = Column(JSON, nullable=True)
    team1_impact = Column(String, nullable=True)
    team2_impact = Column(String, nullable=True)
    
    team1_score = Column(Integer, default=0)
    team1_wickets = Column(Integer, default=0)
    team1_overs = Column(Float, default=0.0)
    
    team2_score = Column(Integer, default=0)
    team2_wickets = Column(Integer, default=0)
    team2_overs = Column(Float, default=0.0)

    tournament = relationship("Tournament", back_populates="matches")
    innings = relationship("Innings", back_populates="match", cascade="all, delete-orphan")

class Innings(Base):
    __tablename__ = "innings"
    id = Column(String, primary_key=True, index=True)
    match_id = Column(String, ForeignKey("matches.id"))
    innings_number = Column(Integer) # 1 or 2
    batting_team_id = Column(String, ForeignKey("teams.id"))
    bowling_team_id = Column(String, ForeignKey("teams.id"))
    runs = Column(Integer, default=0)
    wickets = Column(Integer, default=0)
    overs_bowled = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    
    match = relationship("Match", back_populates="innings")
    events = relationship("MatchEvent", back_populates="innings_obj", cascade="all, delete-orphan")

class MatchEvent(Base):
    __tablename__ = "match_events"
    id = Column(String, primary_key=True, index=True)
    match_id = Column(String, ForeignKey("matches.id"))
    innings_id = Column(String, ForeignKey("innings.id"))
    over_number = Column(Integer)
    ball_number = Column(Integer)
    striker_id = Column(String, ForeignKey("players.id"))
    non_striker_id = Column(String, ForeignKey("players.id"))
    bowler_id = Column(String, ForeignKey("players.id"))
    runs = Column(Integer, default=0)
    extras = Column(Integer, default=0)
    extra_type = Column(String, nullable=True) # WIDE, NOBALL, BYE, LEGBYE
    is_wicket = Column(Boolean, default=False)
    wicket_type = Column(String, nullable=True) # BOWLED, CAUGHT, etc.
    dismissed_player_id = Column(String, ForeignKey("players.id"), nullable=True)
    fielder_id = Column(String, ForeignKey("players.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    commentary = Column(String, nullable=True)
    
    innings_obj = relationship("Innings", back_populates="events")
