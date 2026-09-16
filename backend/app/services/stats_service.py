from sqlalchemy.orm import Session
from .. import models, schemas
from collections import defaultdict
import math

def generate_tournament_stats(db: Session, tournament_id: str) -> schemas.TournamentStatsResponse:
    # 1. Fetch all completed matches for this tournament
    matches = db.query(models.Match).filter(
        models.Match.tournament_id == tournament_id,
        models.Match.status == models.MatchStatus.COMPLETED
    ).all()
    
    match_ids = [m.id for m in matches]
    
    if not match_ids:
        return schemas.TournamentStatsResponse(
            tournament_id=tournament_id,
            batting=[],
            bowling=[],
            fielding=[]
        )
        
    # 2. Fetch all events for these matches
    events = db.query(models.MatchEvent).filter(models.MatchEvent.match_id.in_(match_ids)).all()
    
    # 3. Fetch all players
    players = db.query(models.Player).all()
    players_dict = {p.id: p for p in players}
    
    # Player aggregators
    # Batting: match_id -> runs, balls, 4s, 6s, is_out
    batting_by_match = defaultdict(lambda: defaultdict(lambda: {"runs": 0, "balls": 0, "fours": 0, "sixes": 0, "is_out": False}))
    
    # Bowling: match_id -> balls, runs, wickets
    bowling_by_match = defaultdict(lambda: defaultdict(lambda: {"balls": 0, "runs": 0, "wickets": 0, "maidens": 0}))
    over_runs = defaultdict(int) # (bowler_id, match_id, over_number) -> runs
    
    # Fielding: total catches, run outs, stumpings
    fielding_stats = defaultdict(lambda: {"catches": 0, "run_outs": 0, "stumpings": 0, "matches_played": set()})
    matches_played = defaultdict(set) # player_id -> set of match_ids
    
    for ev in events:
        m_id = ev.match_id
        
        # Track matches played
        matches_played[ev.striker_id].add(m_id)
        matches_played[ev.non_striker_id].add(m_id)
        matches_played[ev.bowler_id].add(m_id)
        
        # Batting
        if ev.extra_type not in ["WIDE"]:
            batting_by_match[ev.striker_id][m_id]["balls"] += 1
            
        if ev.runs > 0 and ev.extra_type not in ["BYE", "LEGBYE", "WIDE"]:
            batting_by_match[ev.striker_id][m_id]["runs"] += ev.runs
            if ev.runs == 4:
                batting_by_match[ev.striker_id][m_id]["fours"] += 1
            elif ev.runs == 6:
                batting_by_match[ev.striker_id][m_id]["sixes"] += 1
                
        # Bowling
        if ev.extra_type not in ["WIDE", "NOBALL"]:
            bowling_by_match[ev.bowler_id][m_id]["balls"] += 1
            
        b_runs = 0
        if ev.extra_type not in ["BYE", "LEGBYE"]:
            b_runs += ev.runs
        if ev.extra_type in ["WIDE", "NOBALL"]:
            b_runs += ev.extras
            
        bowling_by_match[ev.bowler_id][m_id]["runs"] += b_runs
        over_runs[(ev.bowler_id, m_id, ev.over_number)] += b_runs
        
        # Wickets & Fielding
        if ev.is_wicket:
            dis_player = ev.dismissed_player_id
            if dis_player:
                batting_by_match[dis_player][m_id]["is_out"] = True
                
            if ev.wicket_type != "RUN_OUT":
                bowling_by_match[ev.bowler_id][m_id]["wickets"] += 1
                
            if ev.fielder_id:
                matches_played[ev.fielder_id].add(m_id)
                if ev.wicket_type == "CAUGHT":
                    fielding_stats[ev.fielder_id]["catches"] += 1
                elif ev.wicket_type == "STUMPED":
                    fielding_stats[ev.fielder_id]["stumpings"] += 1
                elif ev.wicket_type == "RUN_OUT":
                    fielding_stats[ev.fielder_id]["run_outs"] += 1
                    
    # Calculate maidens
    for (bowler_id, m_id, over_idx), runs in over_runs.items():
        if runs == 0:
            bowling_by_match[bowler_id][m_id]["maidens"] += 1

    # Finalize Batting Stats
    batting_res = []
    for pid, m_stats in batting_by_match.items():
        if pid not in players_dict: continue
        total_runs = sum(s["runs"] for s in m_stats.values())
        total_balls = sum(s["balls"] for s in m_stats.values())
        total_4s = sum(s["fours"] for s in m_stats.values())
        total_6s = sum(s["sixes"] for s in m_stats.values())
        highest_score = max((s["runs"] for s in m_stats.values()), default=0)
        innings = len([s for s in m_stats.values() if s["balls"] > 0 or s["is_out"]])
        not_outs = innings - sum(1 for s in m_stats.values() if s["is_out"])
        
        avg = None
        if (innings - not_outs) > 0:
            avg = round(total_runs / (innings - not_outs), 2)
            
        sr = round((total_runs / total_balls * 100), 2) if total_balls > 0 else 0.0
        
        # Only include if they batted
        if innings > 0:
            batting_res.append(schemas.TournamentBattingStatsSchema(
                player_id=pid,
                name=players_dict[pid].name,
                team_name=players_dict[pid].team_id,
                matches=len(matches_played[pid]),
                innings=innings,
                runs=total_runs,
                balls=total_balls,
                highest_score=highest_score,
                average=avg,
                strike_rate=sr,
                fours=total_4s,
                sixes=total_6s,
                not_outs=not_outs
            ))
            
    # Tie breakers: Runs (desc), SR (desc), Avg (desc)
    batting_res.sort(key=lambda x: (x.runs, x.strike_rate, x.average or 0), reverse=True)
    
    # Finalize Bowling Stats
    bowling_res = []
    for pid, m_stats in bowling_by_match.items():
        if pid not in players_dict: continue
        total_balls = sum(s["balls"] for s in m_stats.values())
        total_runs = sum(s["runs"] for s in m_stats.values())
        total_wickets = sum(s["wickets"] for s in m_stats.values())
        total_maidens = sum(s["maidens"] for s in m_stats.values())
        innings = len([s for s in m_stats.values() if s["balls"] > 0])
        
        best_match = max(m_stats.values(), key=lambda x: (x["wickets"], -x["runs"]), default=None)
        best_bowling = f"{best_match['wickets']}/{best_match['runs']}" if best_match else "0/0"
        
        overs_val = float(f"{total_balls // 6}.{total_balls % 6}")
        econ = round((total_runs / total_balls * 6), 2) if total_balls > 0 else 0.0
        
        if innings > 0:
            bowling_res.append(schemas.TournamentBowlingStatsSchema(
                player_id=pid,
                name=players_dict[pid].name,
                team_name=players_dict[pid].team_id,
                matches=len(matches_played[pid]),
                innings=innings,
                overs=overs_val,
                maidens=total_maidens,
                runs_conceded=total_runs,
                wickets=total_wickets,
                best_bowling=best_bowling,
                economy=econ
            ))
            
    # Tie breakers: Wickets (desc), Economy (asc)
    bowling_res.sort(key=lambda x: (x.wickets, -x.economy), reverse=True)
    
    # Finalize Fielding Stats
    fielding_res = []
    for pid, stats in fielding_stats.items():
        if pid not in players_dict: continue
        if stats["catches"] > 0 or stats["stumpings"] > 0 or stats["run_outs"] > 0:
            fielding_res.append(schemas.TournamentFieldingStatsSchema(
                player_id=pid,
                name=players_dict[pid].name,
                team_name=players_dict[pid].team_id,
                matches=len(matches_played[pid]),
                catches=stats["catches"],
                run_outs=stats["run_outs"],
                stumpings=stats["stumpings"]
            ))
            
    fielding_res.sort(key=lambda x: (x.catches + x.run_outs + x.stumpings), reverse=True)

    return schemas.TournamentStatsResponse(
        tournament_id=tournament_id,
        batting=batting_res,
        bowling=bowling_res,
        fielding=fielding_res
    )
