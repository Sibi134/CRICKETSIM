from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PlayerRatingsSchema(BaseModel):
    batting: int = Field(..., ge=0, le=100)
    power: int = Field(..., ge=0, le=100)
    consistency: int = Field(..., ge=0, le=100)
    running: int = Field(..., ge=0, le=100)
    fielding: int = Field(..., ge=0, le=100)
    bowling: int = Field(..., ge=0, le=100)
    pace: int = Field(..., ge=0, le=100)
    spin: int = Field(..., ge=0, le=100)
    deathBowling: int = Field(..., ge=0, le=100)

class PlayerSchema(BaseModel):
    id: str
    name: str
    nationality: Optional[str] = None
    is_overseas: bool = Field(False, alias="isOverseas")
    role: Optional[str] = None
    primary_skill: Optional[str] = Field(None, alias="primarySkill")
    secondary_skill: Optional[str] = Field(None, alias="secondarySkill")
    batting_style: Optional[str] = Field(None, alias="battingStyle")
    bowling_style: Optional[str] = Field(None, alias="bowlingStyle")
    availability: bool = True
    availability_reason: str = Field("Available", alias="availabilityReason")
    is_captain: bool = Field(False, alias="isCaptain")
    is_vice_captain: bool = Field(False, alias="isViceCaptain")
    rating_status: str = Field("UNRATED", alias="ratingStatus")
    ratings: Optional[PlayerRatingsSchema] = None

    class Config:
        from_attributes = True
        populate_by_name = True

class PlayerUpdateSchema(BaseModel):
    name: Optional[str] = None
    nationality: Optional[str] = None
    is_overseas: Optional[bool] = Field(None, alias="isOverseas")
    role: Optional[str] = None
    primary_skill: Optional[str] = Field(None, alias="primarySkill")
    secondary_skill: Optional[str] = Field(None, alias="secondarySkill")
    batting_style: Optional[str] = Field(None, alias="battingStyle")
    bowling_style: Optional[str] = Field(None, alias="bowlingStyle")
    availability: Optional[bool] = None
    availability_reason: Optional[str] = Field(None, alias="availabilityReason")
    is_captain: Optional[bool] = Field(None, alias="isCaptain")
    is_vice_captain: Optional[bool] = Field(None, alias="isViceCaptain")
    rating_status: Optional[str] = Field(None, alias="ratingStatus")
    ratings: Optional[PlayerRatingsSchema] = None

class PlayerAIOuputSchema(BaseModel):
    name: str
    role: str
    primarySkill: str
    secondarySkill: Optional[str] = None
    isWicketkeeper: bool
    battingStyle: Optional[str] = None
    bowlingStyle: Optional[str] = None
    ratings: PlayerRatingsSchema
    confidence: str

class TeamImportSchema(BaseModel):
    id: str
    name: str
    short_name: str = Field(..., alias="shortName")
    captain_id: Optional[str] = Field(None, alias="captain")
    home_ground: Optional[str] = Field(None, alias="homeGround")
    primary_color: str = Field("#000000", alias="primaryColor")
    secondary_color: str = Field("#ffffff", alias="secondaryColor")

    class Config:
        from_attributes = True
        populate_by_name = True

class TeamImportRequest(BaseModel):
    team: TeamImportSchema
    players: List[PlayerSchema]

class SquadPasteSchema(BaseModel):
    player_names: List[str]
    replace: bool = False

class TeamResponse(TeamImportSchema):
    players: List[PlayerSchema] = []

    class Config:
        from_attributes = True

class TournamentCreate(BaseModel):
    name: str
    overs_per_innings: int = 20
    points_win: int = 2
    points_tie: int = 1
    points_nr: int = 1
    max_overseas_players: int = 4
    impact_player_enabled: bool = True

class TournamentResponse(TournamentCreate):
    id: str
    status: str

    class Config:
        from_attributes = True

class MatchResponse(BaseModel):
    id: str
    tournament_id: str
    match_number: int
    team1_id: str
    team2_id: str
    venue: str
    status: str
    toss_winner: Optional[str] = None
    toss_decision: Optional[str] = None
    winner: Optional[str] = None
    result_type: Optional[str] = None
    
    team1_score: int
    team1_wickets: int
    team1_overs: float
    
    team2_score: int
    team2_wickets: int
    team2_overs: float
    
    scheduled_date: datetime
    team1_xi: Optional[List[str]] = None
    team2_xi: Optional[List[str]] = None
    team1_impact: Optional[str] = None
    team2_impact: Optional[str] = None

    class Config:
        from_attributes = True

class PlayingXISchema(BaseModel):
    playing_xi: List[str]
    impact_player: Optional[str] = None

class TossSchema(BaseModel):
    winner_id: str
    decision: str # BAT or FIELD

class BatterScorecardSchema(BaseModel):
    player_id: str
    name: str
    runs: int
    balls: int
    fours: int
    sixes: int
    strike_rate: float
    dismissal: str
    is_out: bool

class BowlerScorecardSchema(BaseModel):
    player_id: str
    name: str
    overs: float
    maidens: int
    runs: int
    wickets: int
    economy: float

class ExtrasScorecardSchema(BaseModel):
    wides: int
    noballs: int
    byes: int
    legbyes: int
    total: int

class InningsScorecardSchema(BaseModel):
    team_id: str
    team_name: str
    batting: List[BatterScorecardSchema]
    bowling: List[BowlerScorecardSchema]
    extras: ExtrasScorecardSchema
    total_runs: int
    total_wickets: int
    total_overs: float
    run_rate: float

class MatchScorecardResponse(BaseModel):
    match_id: str
    status: str
    innings1: Optional[InningsScorecardSchema] = None
    innings2: Optional[InningsScorecardSchema] = None
    result_string: Optional[str] = None
    player_of_match_id: Optional[str] = None
    player_of_match_name: Optional[str] = None
    player_of_match_summary: Optional[str] = None

class TournamentBattingStatsSchema(BaseModel):
    player_id: str
    name: str
    team_name: str
    matches: int
    innings: int
    runs: int
    balls: int
    highest_score: int
    average: Optional[float]
    strike_rate: float
    fours: int
    sixes: int
    not_outs: int

class TournamentBowlingStatsSchema(BaseModel):
    player_id: str
    name: str
    team_name: str
    matches: int
    innings: int
    overs: float
    maidens: int
    runs_conceded: int
    wickets: int
    best_bowling: str
    economy: float

class TournamentFieldingStatsSchema(BaseModel):
    player_id: str
    name: str
    team_name: str
    matches: int
    catches: int
    run_outs: int
    stumpings: int

class TournamentStatsResponse(BaseModel):
    tournament_id: str
    batting: List[TournamentBattingStatsSchema]
    bowling: List[TournamentBowlingStatsSchema]
    fielding: List[TournamentFieldingStatsSchema]
