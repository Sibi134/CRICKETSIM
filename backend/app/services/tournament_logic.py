from sqlalchemy.orm import Session
from .. import models
from collections import defaultdict

def calculate_standings(db: Session, tournament_id: str):
    matches = db.query(models.Match).filter(
        models.Match.tournament_id == tournament_id,
        models.Match.status == models.MatchStatus.COMPLETED
    ).all()
    
    standings = defaultdict(lambda: {"played": 0, "won": 0, "lost": 0, "tied": 0, "nr": 0, "points": 0, "runs_scored": 0, "overs_faced": 0.0, "runs_conceded": 0, "overs_bowled": 0.0})
    
    # Initialize all teams
    tournament = db.query(models.Tournament).filter(models.Tournament.id == tournament_id).first()
    # (If we wanted to show all teams even with 0 matches)
    
    points_win = tournament.points_win
    points_tie = tournament.points_tie
    points_nr = tournament.points_nr
    
    for match in matches:
        t1 = match.team1_id
        t2 = match.team2_id
        
        standings[t1]["played"] += 1
        standings[t2]["played"] += 1
        
        if match.winner == t1:
            standings[t1]["won"] += 1
            standings[t1]["points"] += points_win
            standings[t2]["lost"] += 1
        elif match.winner == t2:
            standings[t2]["won"] += 1
            standings[t2]["points"] += points_win
            standings[t1]["lost"] += 1
        elif match.result_type == "TIE":
            standings[t1]["tied"] += 1
            standings[t2]["tied"] += 1
            standings[t1]["points"] += points_tie
            standings[t2]["points"] += points_tie
        else:
            standings[t1]["nr"] += 1
            standings[t2]["nr"] += 1
            standings[t1]["points"] += points_nr
            standings[t2]["points"] += points_nr
            
        # NRR Calculation logic
        # Note: All out innings should count as full overs (e.g. 20) for NRR
        max_overs = tournament.overs_per_innings
        
        t1_overs_faced = match.team1_overs if match.team1_wickets < 10 else float(max_overs)
        t2_overs_faced = match.team2_overs if match.team2_wickets < 10 else float(max_overs)
        
        standings[t1]["runs_scored"] += match.team1_score
        standings[t1]["overs_faced"] += t1_overs_faced
        standings[t1]["runs_conceded"] += match.team2_score
        standings[t1]["overs_bowled"] += t2_overs_faced
        
        standings[t2]["runs_scored"] += match.team2_score
        standings[t2]["overs_faced"] += t2_overs_faced
        standings[t2]["runs_conceded"] += match.team1_score
        standings[t2]["overs_bowled"] += t1_overs_faced

    # Format result and calculate NRR
    result = []
    for team_id, stats in standings.items():
        team_nrr = 0.0
        if stats["overs_faced"] > 0 and stats["overs_bowled"] > 0:
            team_nrr = (stats["runs_scored"] / stats["overs_faced"]) - (stats["runs_conceded"] / stats["overs_bowled"])
            
        result.append({
            "team_id": team_id,
            "played": stats["played"],
            "won": stats["won"],
            "lost": stats["lost"],
            "tied": stats["tied"],
            "nr": stats["nr"],
            "points": stats["points"],
            "nrr": round(team_nrr, 3)
        })
        
    # Sort by Points, then NRR
    result.sort(key=lambda x: (x["points"], x["nrr"]), reverse=True)
    
    # Assign positions
    for i, res in enumerate(result):
        res["position"] = i + 1
        
    return result

def get_player_stats(db: Session, tournament_id: str):
    events = db.query(models.MatchEvent).join(models.Match).filter(
        models.Match.tournament_id == tournament_id
    ).all()
    
    stats = defaultdict(lambda: {
        "runs": 0, "balls_faced": 0, "fours": 0, "sixes": 0, 
        "wickets": 0, "runs_conceded": 0, "balls_bowled": 0
    })
    
    for evt in events:
        # Batting
        if evt.striker_id:
            stats[evt.striker_id]["runs"] += evt.runs
            if not evt.extra_type in ["WIDE"]:
                stats[evt.striker_id]["balls_faced"] += 1
            if evt.runs == 4:
                stats[evt.striker_id]["fours"] += 1
            elif evt.runs == 6:
                stats[evt.striker_id]["sixes"] += 1
                
        # Bowling
        if evt.bowler_id:
            stats[evt.bowler_id]["runs_conceded"] += evt.runs + (evt.extras if evt.extra_type in ["WIDE", "NOBALL"] else 0)
            if not evt.extra_type in ["WIDE", "NOBALL"]:
                stats[evt.bowler_id]["balls_bowled"] += 1
            if evt.is_wicket and evt.wicket_type not in ["RUN OUT"]:
                stats[evt.bowler_id]["wickets"] += 1
                
    # Formatting
    formatted = []
    for pid, s in stats.items():
        sr = (s["runs"] / s["balls_faced"] * 100) if s["balls_faced"] > 0 else 0
        eco = (s["runs_conceded"] / (s["balls_bowled"] / 6)) if s["balls_bowled"] > 0 else 0
        formatted.append({
            "player_id": pid,
            "runs": s["runs"],
            "strike_rate": round(sr, 2),
            "wickets": s["wickets"],
            "economy": round(eco, 2),
            "sixes": s["sixes"],
            "fours": s["fours"]
        })
        
    return formatted
