from sqlalchemy.orm import Session
from .. import models
from collections import defaultdict

def calculate_player_of_match(db: Session, match_id: str) -> str:
    events = db.query(models.MatchEvent).filter(models.MatchEvent.match_id == match_id).all()
    if not events:
        return None
        
    match = db.query(models.Match).filter(models.Match.id == match_id).first()
    
    player_points = defaultdict(float)
    
    # Track balls for strike rate bonus
    batter_balls = defaultdict(int)
    batter_runs = defaultdict(int)
    
    bowler_balls = defaultdict(int)
    bowler_runs = defaultdict(int)
    bowler_wickets = defaultdict(int)
    
    for ev in events:
        # Batting
        if ev.extra_type not in ["WIDE"]:
            batter_balls[ev.striker_id] += 1
            
        if ev.runs > 0 and ev.extra_type not in ["BYE", "LEGBYE", "WIDE"]:
            batter_runs[ev.striker_id] += ev.runs
            player_points[ev.striker_id] += ev.runs # 1 pt per run
            if ev.runs == 6:
                player_points[ev.striker_id] += 2 # Bonus for 6
                
        # Bowling
        if ev.extra_type not in ["WIDE", "NOBALL"]:
            bowler_balls[ev.bowler_id] += 1
            
        # Bowler runs
        b_runs = 0
        if ev.extra_type not in ["BYE", "LEGBYE"]:
            b_runs += ev.runs
        if ev.extra_type in ["WIDE", "NOBALL"]:
            b_runs += ev.extras
        bowler_runs[ev.bowler_id] += b_runs
        
        # Wickets
        if ev.is_wicket:
            if ev.wicket_type != "RUN_OUT":
                bowler_wickets[ev.bowler_id] += 1
                player_points[ev.bowler_id] += 25 # 25 pts per wicket
                
            if ev.fielder_id:
                player_points[ev.fielder_id] += 10 # 10 pts per catch/stumping/run-out
                
    # Apply bonuses
    for pid, runs in batter_runs.items():
        if runs >= 100:
            player_points[pid] += 25
        elif runs >= 50:
            player_points[pid] += 10
            
        balls = batter_balls[pid]
        if balls >= 15:
            sr = (runs / balls) * 100
            if sr >= 200:
                player_points[pid] += 15
            elif sr >= 150:
                player_points[pid] += 10
                
    for pid, wkts in bowler_wickets.items():
        if wkts >= 5:
            player_points[pid] += 30
        elif wkts >= 4:
            player_points[pid] += 20
            
        balls = bowler_balls[pid]
        if balls >= 12: # Min 2 overs
            econ = (bowler_runs[pid] / balls) * 6
            if econ <= 5.0:
                player_points[pid] += 20
            elif econ <= 7.0:
                player_points[pid] += 10
                
    # Winning team bonus (Tiny tie-breaker)
    if match.winner:
        winning_players = db.query(models.Player).filter(models.Player.team_id == match.winner).all()
        for p in winning_players:
            if player_points[p.id] > 0:
                player_points[p.id] += 1.0 # Only 1 point as a tiny tie-breaker
                
    if not player_points:
        return None
        
    # Get player with max points
    best_player_id = max(player_points.items(), key=lambda x: x[1])[0]
    return best_player_id
