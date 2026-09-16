from sqlalchemy.orm import Session
from .. import models, schemas
from collections import defaultdict
import math

def build_innings_scorecard(db: Session, innings: models.Innings, match: models.Match) -> schemas.InningsScorecardSchema:
    events = db.query(models.MatchEvent).filter(
        models.MatchEvent.innings_id == innings.id
    ).order_by(models.MatchEvent.over_number, models.MatchEvent.ball_number).all()
    
    batting_stats = defaultdict(lambda: {"runs": 0, "balls": 0, "fours": 0, "sixes": 0, "is_out": False, "dismissal": "not out"})
    bowling_stats = defaultdict(lambda: {"balls": 0, "runs": 0, "wickets": 0, "maidens": 0})
    extras = {"wides": 0, "noballs": 0, "byes": 0, "legbyes": 0, "total": 0}
    
    # We need player names. Fetch all players in this match
    team1_players = db.query(models.Player).filter(models.Player.team_id == match.team1_id).all()
    team2_players = db.query(models.Player).filter(models.Player.team_id == match.team2_id).all()
    players_dict = {p.id: p for p in team1_players + team2_players}
    
    # Track overs for maidens
    over_runs = defaultdict(int)
    
    for ev in events:
        # Batting
        if ev.striker_id not in batting_stats:
            batting_stats[ev.striker_id]["name"] = players_dict[ev.striker_id].name if ev.striker_id in players_dict else "Unknown"
        if ev.non_striker_id not in batting_stats:
            batting_stats[ev.non_striker_id]["name"] = players_dict[ev.non_striker_id].name if ev.non_striker_id in players_dict else "Unknown"
            
        if ev.extra_type not in ["WIDE"]:
            batting_stats[ev.striker_id]["balls"] += 1
            
        if ev.runs > 0 and ev.extra_type not in ["BYE", "LEGBYE", "WIDE"]:
            batting_stats[ev.striker_id]["runs"] += ev.runs
            if ev.runs == 4:
                batting_stats[ev.striker_id]["fours"] += 1
            elif ev.runs == 6:
                batting_stats[ev.striker_id]["sixes"] += 1
                
        # Bowling
        if ev.bowler_id not in bowling_stats:
            bowling_stats[ev.bowler_id]["name"] = players_dict[ev.bowler_id].name if ev.bowler_id in players_dict else "Unknown"
            
        if ev.extra_type not in ["WIDE", "NOBALL"]:
            bowling_stats[ev.bowler_id]["balls"] += 1
            
        # Bowler runs: batter runs + wides + noballs
        bowler_runs = 0
        if ev.extra_type not in ["BYE", "LEGBYE"]:
            bowler_runs += ev.runs
        if ev.extra_type in ["WIDE", "NOBALL"]:
            bowler_runs += ev.extras
            
        bowling_stats[ev.bowler_id]["runs"] += bowler_runs
        over_runs[(ev.bowler_id, ev.over_number)] += bowler_runs
        
        # Extras
        if ev.extra_type == "WIDE":
            extras["wides"] += ev.extras
            extras["total"] += ev.extras
        elif ev.extra_type == "NOBALL":
            extras["noballs"] += ev.extras
            extras["total"] += ev.extras
        elif ev.extra_type == "BYE":
            extras["byes"] += ev.extras
            extras["total"] += ev.extras
        elif ev.extra_type == "LEGBYE":
            extras["legbyes"] += ev.extras
            extras["total"] += ev.extras
            
        # Wickets
        if ev.is_wicket:
            if ev.wicket_type != "RUN_OUT":
                bowling_stats[ev.bowler_id]["wickets"] += 1
            
            dis_player = ev.dismissed_player_id
            if dis_player:
                batting_stats[dis_player]["is_out"] = True
                
                # Construct dismissal string
                bowler_name = players_dict[ev.bowler_id].name if ev.bowler_id in players_dict else "Bowler"
                fielder_name = players_dict[ev.fielder_id].name if ev.fielder_id and ev.fielder_id in players_dict else None
                
                if ev.wicket_type == "BOWLED":
                    batting_stats[dis_player]["dismissal"] = f"b {bowler_name}"
                elif ev.wicket_type == "LBW":
                    batting_stats[dis_player]["dismissal"] = f"lbw b {bowler_name}"
                elif ev.wicket_type == "CAUGHT":
                    if fielder_name:
                        batting_stats[dis_player]["dismissal"] = f"c {fielder_name} b {bowler_name}"
                    else:
                        batting_stats[dis_player]["dismissal"] = f"c & b {bowler_name}"
                elif ev.wicket_type == "STUMPED":
                    if fielder_name:
                        batting_stats[dis_player]["dismissal"] = f"st {fielder_name} b {bowler_name}"
                    else:
                        batting_stats[dis_player]["dismissal"] = f"st b {bowler_name}"
                elif ev.wicket_type == "RUN_OUT":
                    if fielder_name:
                        batting_stats[dis_player]["dismissal"] = f"run out ({fielder_name})"
                    else:
                        batting_stats[dis_player]["dismissal"] = "run out"
                else:
                    batting_stats[dis_player]["dismissal"] = "out"

    # Calculate Maidens
    for (bowler_id, over_idx), runs in over_runs.items():
        if runs == 0:
            bowling_stats[bowler_id]["maidens"] += 1
            
    # Format Batting output
    batters_list = []
    # To keep order, we sort by balls > 0 or is_out
    for pid, stats in batting_stats.items():
        sr = (stats["runs"] / stats["balls"] * 100) if stats["balls"] > 0 else 0.0
        batters_list.append(schemas.BatterScorecardSchema(
            player_id=pid,
            name=stats.get("name", "Unknown"),
            runs=stats["runs"],
            balls=stats["balls"],
            fours=stats["fours"],
            sixes=stats["sixes"],
            strike_rate=round(sr, 2),
            dismissal=stats["dismissal"],
            is_out=stats["is_out"]
        ))
    
    # Sort batters (out first or most balls)
    # Ideally, sorted by entry order but we can approximate by runs/balls
    batters_list.sort(key=lambda x: (-x.balls, -x.runs))
    
    # Format Bowling output
    bowlers_list = []
    for pid, stats in bowling_stats.items():
        completed_overs = stats["balls"] // 6
        extra_balls = stats["balls"] % 6
        overs_str = float(f"{completed_overs}.{extra_balls}")
        
        econ = (stats["runs"] / stats["balls"] * 6) if stats["balls"] > 0 else 0.0
        
        bowlers_list.append(schemas.BowlerScorecardSchema(
            player_id=pid,
            name=stats.get("name", "Unknown"),
            overs=overs_str,
            maidens=stats["maidens"],
            runs=stats["runs"],
            wickets=stats["wickets"],
            economy=round(econ, 2)
        ))
        
    team_name = match.team1_id if innings.batting_team_id == match.team1_id else match.team2_id
    
    run_rate = (innings.runs / innings.overs_bowled) if innings.overs_bowled > 0 else 0.0
    
    return schemas.InningsScorecardSchema(
        team_id=innings.batting_team_id,
        team_name=team_name,
        batting=batters_list,
        bowling=bowlers_list,
        extras=schemas.ExtrasScorecardSchema(**extras),
        total_runs=innings.runs,
        total_wickets=innings.wickets,
        total_overs=innings.overs_bowled,
        run_rate=round(run_rate, 2)
    )

def generate_match_scorecard(db: Session, match: models.Match) -> schemas.MatchScorecardResponse:
    # Fetch innings
    innings1 = db.query(models.Innings).filter(models.Innings.match_id == match.id, models.Innings.innings_number == 1).first()
    innings2 = db.query(models.Innings).filter(models.Innings.match_id == match.id, models.Innings.innings_number == 2).first()
    
    sc1 = build_innings_scorecard(db, innings1, match) if innings1 else None
    sc2 = build_innings_scorecard(db, innings2, match) if innings2 else None
    
    result_string = None
    if match.status == models.MatchStatus.COMPLETED:
        if match.winner:
            if match.winner == match.team1_id:
                margin = match.team1_score - match.team2_score
                result_string = f"{match.team1_id} won by {margin} runs" if sc1 and sc1.team_id == match.team1_id else f"{match.team1_id} won by {10 - match.team1_wickets} wickets"
            else:
                margin = match.team2_score - match.team1_score
                result_string = f"{match.team2_id} won by {margin} runs" if sc1 and sc1.team_id == match.team2_id else f"{match.team2_id} won by {10 - match.team2_wickets} wickets"
        else:
            result_string = "Match Tied"
            
    player_of_match_id = None
    player_of_match_name = None
    player_of_match_summary = None
    
    if match.player_of_match:
        player_of_match_id = match.player_of_match
        pom_player = db.query(models.Player).filter(models.Player.id == match.player_of_match).first()
        if pom_player:
            player_of_match_name = f"{pom_player.name} — {pom_player.team_id}"
            
            # Find stats for this player from sc1 and sc2
            runs = 0
            balls = 0
            wickets = 0
            overs = 0.0
            runs_conceded = 0
            
            for sc in [sc1, sc2]:
                if not sc: continue
                for b in sc.batting:
                    if b.player_id == player_of_match_id:
                        runs += b.runs
                        balls += b.balls
                for b in sc.bowling:
                    if b.player_id == player_of_match_id:
                        wickets += b.wickets
                        overs += b.overs
                        runs_conceded += b.runs
                        
            summary_parts = []
            if balls > 0 or runs > 0:
                summary_parts.append(f"{runs} runs ({balls} balls)")
            if overs > 0:
                summary_parts.append(f"{wickets}/{runs_conceded} ({overs} overs)")
            if not summary_parts:
                summary_parts.append("Excellent fielding/captaincy")
                
            player_of_match_summary = " & ".join(summary_parts)
            
    return schemas.MatchScorecardResponse(
        match_id=match.id,
        status=match.status,
        innings1=sc1,
        innings2=sc2,
        result_string=result_string,
        player_of_match_id=player_of_match_id,
        player_of_match_name=player_of_match_name,
        player_of_match_summary=player_of_match_summary
    )
