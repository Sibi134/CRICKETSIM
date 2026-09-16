from sqlalchemy.orm import Session
from ... import models
from .probability import ProbabilityEngine
from ..awards import calculate_player_of_match
import uuid
from datetime import datetime

class MatchSimulationEngine:
    def __init__(self, db: Session, match: models.Match):
        self.db = db
        self.match = match
        self.seed = match.simulation_seed or int(datetime.utcnow().timestamp())
        if not match.simulation_seed:
            match.simulation_seed = self.seed
            db.commit()
            
        self.prob_engine = ProbabilityEngine(self.seed)

    def get_phase(self, over: int, max_overs: int) -> str:
        if over < 6:
            return "POWERPLAY"
        elif over >= max_overs - 4:
            return "DEATH"
        return "MIDDLE"

    def simulate_overs(self, num_overs: int):
        """Simulate a specified number of overs or until innings ends."""
        # Find active innings
        innings = self.db.query(models.Innings).filter(
            models.Innings.match_id == self.match.id,
            models.Innings.is_completed == False
        ).order_by(models.Innings.innings_number).first()
        
        if not innings:
            # Check if previous innings exist
            existing_innings = self.db.query(models.Innings).filter(
                models.Innings.match_id == self.match.id
            ).order_by(models.Innings.innings_number.desc()).first()
            
            if not existing_innings:
                # Need to create first innings
                if not self.match.toss_winner or not self.match.toss_decision:
                    raise ValueError("Toss not conducted")
                    
                batting_team = self.match.toss_winner if self.match.toss_decision == "BAT" else (
                    self.match.team1_id if self.match.toss_winner == self.match.team2_id else self.match.team2_id
                )
                bowling_team = self.match.team1_id if batting_team == self.match.team2_id else self.match.team2_id
                
                innings = models.Innings(
                    id=f"INN_{uuid.uuid4().hex[:8].upper()}",
                    match_id=self.match.id,
                    innings_number=1,
                    batting_team_id=batting_team,
                    bowling_team_id=bowling_team
                )
            elif existing_innings.innings_number == 1 and existing_innings.is_completed:
                # Create second innings
                innings = models.Innings(
                    id=f"INN_{uuid.uuid4().hex[:8].upper()}",
                    match_id=self.match.id,
                    innings_number=2,
                    batting_team_id=existing_innings.bowling_team_id,
                    bowling_team_id=existing_innings.batting_team_id
                )
            else:
                raise ValueError("Match is already completed")
                
            self.db.add(innings)
            self.db.commit()
            self.db.refresh(innings)

        max_overs = self.match.tournament.overs_per_innings
        target = None
        if innings.innings_number == 2:
            first_innings = self.db.query(models.Innings).filter(
                models.Innings.match_id == self.match.id,
                models.Innings.innings_number == 1
            ).first()
            target = first_innings.runs + 1

        overs_to_sim = min(num_overs, max_overs - int(innings.overs_bowled))
        
        # We need actual players in the exact order of the Playing XI
        batting_team_xi_ids = self.match.team1_xi if innings.batting_team_id == self.match.team1_id else self.match.team2_xi
        batters_unordered = self.db.query(models.Player).filter(models.Player.id.in_(batting_team_xi_ids)).all()
        # Sort batters by their index in the playing XI array
        batters = sorted(batters_unordered, key=lambda p: batting_team_xi_ids.index(p.id))
        
        fielding_team_xi_ids = self.match.team1_xi if innings.bowling_team_id == self.match.team1_id else self.match.team2_xi
        bowlers_unordered = self.db.query(models.Player).filter(models.Player.id.in_(fielding_team_xi_ids)).all()
        # Sort bowlers by index as well just in case
        bowlers_all = sorted(bowlers_unordered, key=lambda p: fielding_team_xi_ids.index(p.id))
        
        # Valid bowling roles
        valid_bowling_roles = ["Fast Bowler", "Spin Bowler", "Bowling All-rounder", "All-rounder"]
        valid_bowlers = [p for p in bowlers_all if p.role in valid_bowling_roles]
        
        # Fallback if somehow there are fewer than 6 valid bowlers (to prevent consecutive over traps)
        if len(valid_bowlers) < 6:
            # Add batters who might bowl part-time, excluding wicketkeepers entirely
            part_timers = [p for p in bowlers_all if p not in valid_bowlers and not (p.role and 'Wicketkeeper' in p.role)]
            valid_bowlers.extend(part_timers[:6 - len(valid_bowlers)])
            
        # If we STILL have less than 6 (extreme edge case), we just add anyone who isn't the primary wk
        wk = next((p for p in bowlers_all if p.role and 'Wicketkeeper' in p.role), bowlers_all[0])
        if len(valid_bowlers) < 6:
            remaining = [p for p in bowlers_all if p not in valid_bowlers and p.id != wk.id]
            valid_bowlers.extend(remaining[:6 - len(valid_bowlers)])
            
        if not batters or not bowlers_all:
            raise ValueError("Playing XI not fully selected")

        current_over = int(innings.overs_bowled)
        current_ball = int((innings.overs_bowled - current_over) * 10)
        
        balls_to_sim = overs_to_sim * 6
        
        # T20 bowling limits
        from collections import defaultdict
        # Fetch existing bowler balls for this innings to support chunked simulation properly
        bowler_balls = defaultdict(int)
        existing_events = self.db.query(models.MatchEvent).filter(
            models.MatchEvent.match_id == self.match.id,
            models.MatchEvent.innings_id == innings.id,
            models.MatchEvent.extra_type.notin_(['WIDE', 'NOBALL'])
        ).all()
        for e in existing_events:
            if e.bowler_id:
                bowler_balls[e.bowler_id] += 1
                
        # VERY basic state
        striker = batters[0]
        non_striker = batters[1]
        
        # Pick opening bowler
        bowler = valid_bowlers[0]
        previous_bowler = None
        
        target_over = current_over + overs_to_sim
        
        while current_over < target_over and innings.wickets < 10:
            if innings.wickets >= 10:
                innings.is_completed = True
                break
                
            if target and innings.runs >= target:
                innings.is_completed = True
                break
                
            phase = self.get_phase(current_over, max_overs)
            rrr = None
            if target:
                runs_req = target - innings.runs
                balls_left = (max_overs * 6) - (current_over * 6 + current_ball)
                if balls_left > 0:
                    rrr = (runs_req / balls_left) * 6
            
            context = {
                "batter": striker.ratings,
                "bowler": bowler.ratings,
                "phase": phase,
                "rrr": rrr,
                "fielders": [p.id for p in bowlers_all if p.id != bowler.id and p.id != wk.id],
                "wk_id": wk.id
            }
            
            outcome = self.prob_engine.calculate_delivery_outcome(context)
            
            event = models.MatchEvent(
                id=f"EVT_{uuid.uuid4().hex[:8].upper()}",
                match_id=self.match.id,
                innings_id=innings.id,
                over_number=current_over,
                ball_number=current_ball + 1,
                striker_id=striker.id,
                non_striker_id=non_striker.id,
                bowler_id=bowler.id,
                runs=outcome['runs'],
                extras=outcome['extras'],
                extra_type=outcome.get('extra_type'),
                is_wicket=outcome['wicket'],
                wicket_type=outcome.get('wicket_type'),
                dismissed_player_id=striker.id if outcome['wicket'] else None,
                fielder_id=outcome.get('fielder_id')
            )
            
            innings.runs += outcome['runs'] + outcome['extras']
            if outcome['wicket']:
                innings.wickets += 1
                # Simplified next batter
                if innings.wickets < 10 and innings.wickets + 1 < len(batters):
                    striker = batters[innings.wickets + 1]
            
            # Strike rotation logic
            if not outcome.get('extra_type') in ['WIDE', 'NOBALL']:
                current_ball += 1
                bowler_balls[bowler.id] += 1
                
                if outcome['runs'] % 2 != 0:
                    striker, non_striker = non_striker, striker # Rotate strike
                    
                if current_ball == 6:
                    current_over += 1
                    current_ball = 0
                    striker, non_striker = non_striker, striker # Rotate end of over
                    
                    # Bowler change logic (Max 4 overs per bowler in T20)
                    previous_bowler = bowler
                    available_bowlers = [b for b in valid_bowlers if b.id != previous_bowler.id and bowler_balls[b.id] < 24]
                    if available_bowlers:
                        bowler = self.prob_engine.rng.choice(available_bowlers)
                    else:
                        # Fallback if everyone bowled out or trapped
                        fallback = [b for b in bowlers_all if b.id != previous_bowler.id and b.id != wk.id and bowler_balls[b.id] < 24]
                        if fallback:
                            bowler = self.prob_engine.rng.choice(fallback)
                        else:
                            super_fallback = [b for b in bowlers_all if b.id != previous_bowler.id and bowler_balls[b.id] < 24]
                            if super_fallback:
                                bowler = self.prob_engine.rng.choice(super_fallback)
                            else:
                                bowler = self.prob_engine.rng.choice([b for b in bowlers_all if b.id != previous_bowler.id])
            
            innings.overs_bowled = current_over + (current_ball / 10.0)
            self.db.add(event)
            
            if current_over >= max_overs:
                innings.is_completed = True
                break

        # Update Match score state
        if innings.batting_team_id == self.match.team1_id:
            self.match.team1_score = innings.runs
            self.match.team1_wickets = innings.wickets
            self.match.team1_overs = innings.overs_bowled
        else:
            self.match.team2_score = innings.runs
            self.match.team2_wickets = innings.wickets
            self.match.team2_overs = innings.overs_bowled
            
        if innings.is_completed:
            if innings.innings_number == 1:
                # We do not have current_innings in match, the second innings is created at start of next call
                self.match.target_score = innings.runs + 1
            else:
                self.match.status = models.MatchStatus.COMPLETED
                
                # Determine winner
                if self.match.team1_score > self.match.team2_score:
                    self.match.winner = self.match.team1_id
                elif self.match.team2_score > self.match.team1_score:
                    self.match.winner = self.match.team2_id
                else:
                    pass # Tie
                    
                # Assign Player of the Match
                self.match.player_of_match = calculate_player_of_match(self.db, self.match.id)

        self.db.commit()
        return innings
