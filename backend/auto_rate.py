import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.database import SessionLocal
from app import models
from app.services import ai_rating

db = SessionLocal()

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def re_evaluate_players():
    # Get all players
    players = db.query(models.Player).all()
    print(f"Found {len(players)} players to evaluate.")
    
    updated_count = 0
    # Process in chunks to avoid overwhelming the LLM and hitting limits
    for chunk in chunk_list(players, 20):
        names = []
        player_map = {}
        for p in chunk:
            name_clean = p.name.replace(" (C)", "").replace(" (VC)", "").replace(" (WK)", "").strip()
            names.append(name_clean)
            player_map[name_clean] = p
            
        print(f"Analyzing chunk of {len(names)} players...")
        try:
            results = ai_rating.analyze_players(names)
        except Exception as e:
            print(f"Error analyzing chunk: {e}")
            continue
            
        for name_clean, ai_data in results.items():
            player = player_map.get(name_clean)
            if not player:
                continue
                
            player.role = ai_data.role
            player.primary_skill = ai_data.primarySkill
            player.secondary_skill = ai_data.secondarySkill
            player.batting_style = ai_data.battingStyle
            player.bowling_style = ai_data.bowlingStyle
            player.ratings = ai_data.ratings.dict()
            player.rating_status = "READY" if ai_rating.validate_ratings(ai_data) else "REVIEW_REQUIRED"
            
            updated_count += 1
            
        # Commit after each chunk
        db.commit()
        
    print(f"Successfully auto-rated and updated {updated_count} players.")

if __name__ == "__main__":
    re_evaluate_players()
