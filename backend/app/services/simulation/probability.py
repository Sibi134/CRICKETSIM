import random

class ProbabilityEngine:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)

    def calculate_delivery_outcome(self, context: dict) -> dict:
        """
        Calculate outcome based on batter ratings, bowler ratings, pitch, match phase, etc.
        Context includes:
        - batter: dict of ratings
        - bowler: dict of ratings
        - phase: 'POWERPLAY', 'MIDDLE', 'DEATH'
        - rrr: float (Required Run Rate, if chasing, else None)
        """
        b_ratings = context['batter']
        bl_ratings = context['bowler']
        phase = context['phase']
        rrr = context.get('rrr', None)
        
        # Base probabilities
        # [0, 1, 2, 3, 4, 6, W, WIDE, NOBALL]
        # Using a dictionary for clarity
        probs = {
            "0": 35.0,
            "1": 30.0,
            "2": 8.0,
            "3": 1.0,
            "4": 12.0,
            "6": 5.0,
            "W": 4.0,
            "WD": 4.0,
            "NB": 1.0
        }

        # Apply Batter Power & Consistency
        power_bonus = (b_ratings.get('power', 50) - 50) / 10.0 # -5 to +5
        probs["6"] += power_bonus
        probs["4"] += power_bonus * 0.8
        
        cons_bonus = (b_ratings.get('consistency', 50) - 50) / 10.0
        probs["W"] -= cons_bonus
        probs["0"] -= cons_bonus * 0.5
        probs["1"] += cons_bonus * 0.5
        
        # Apply Bowler Skill
        bowl_skill = (bl_ratings.get('bowling', 50) - 50) / 10.0
        probs["0"] += bowl_skill
        probs["W"] += bowl_skill * 0.5
        probs["4"] -= bowl_skill * 0.5
        probs["6"] -= bowl_skill * 0.5
        
        # Apply Phase
        if phase == 'POWERPLAY':
            probs["4"] *= 1.3
            probs["6"] *= 1.2
            probs["0"] *= 1.1
            probs["1"] *= 0.8
        elif phase == 'DEATH':
            probs["6"] *= 1.5
            probs["4"] *= 1.3
            probs["W"] *= 1.4
            probs["0"] *= 1.2
            probs["1"] *= 0.7
            # Death bowling skill
            death_skill = (bl_ratings.get('deathBowling', 50) - 50) / 10.0
            probs["W"] += death_skill * 0.5
            probs["6"] -= death_skill * 0.5
        
        # Apply Match Situation (RRR)
        if rrr and rrr > 0:
            aggression = min(max((rrr - 8.0) / 4.0, 0), 2.0) # 0 to 2 multiplier based on how high RRR is
            probs["6"] *= (1 + aggression)
            probs["4"] *= (1 + aggression * 0.8)
            probs["W"] *= (1 + aggression * 0.9)
            probs["0"] *= max(0.5, 1 - aggression * 0.2)
        
        # Normalize probabilities and prevent negatives
        total_prob = 0
        for k in probs:
            probs[k] = max(probs[k], 0.1) # Floor at 0.1%
            total_prob += probs[k]
            
        # Select outcome
        rand_val = self.rng.uniform(0, total_prob)
        cumulative = 0.0
        for k, v in probs.items():
            cumulative += v
            if rand_val <= cumulative:
                return self._parse_outcome(k, context)
                
        return self._parse_outcome("0", context) # Fallback
        
    def _parse_outcome(self, key: str, context: dict) -> dict:
        if key in ["0", "1", "2", "3", "4", "6"]:
            return {"runs": int(key), "extras": 0, "wicket": False}
        elif key == "W":
            # Determine realistic dismissal
            d_rand = self.rng.uniform(0, 100)
            fielder_id = None
            if d_rand < 15.0:
                wt = "BOWLED"
            elif d_rand < 25.0:
                wt = "LBW"
            elif d_rand < 30.0:
                wt = "RUN_OUT"
                # Pick random fielder for run out (could be anyone including wk)
                all_fielders = context.get('fielders', []) + [context.get('wk_id')]
                if all_fielders and all_fielders[0]:
                    fielder_id = self.rng.choice([f for f in all_fielders if f])
            elif d_rand < 35.0:
                wt = "STUMPED"
                fielder_id = context.get('wk_id')
            else:
                wt = "CAUGHT"
                # 30% chance caught by keeper, 70% by other fielders
                if context.get('wk_id') and self.rng.uniform(0, 100) < 30:
                    fielder_id = context.get('wk_id')
                elif context.get('fielders'):
                    fielder_id = self.rng.choice(context.get('fielders'))
                else:
                    fielder_id = context.get('wk_id')
                
            return {"runs": 0, "extras": 0, "wicket": True, "wicket_type": wt, "fielder_id": fielder_id}
        elif key == "WD":
            return {"runs": 0, "extras": 1, "extra_type": "WIDE", "wicket": False}
        elif key == "NB":
            return {"runs": 0, "extras": 1, "extra_type": "NOBALL", "wicket": False}
        return {"runs": 0, "extras": 0, "wicket": False}
