import os
import json
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ValidationError

class PlayerRatingsSchema(BaseModel):
    batting: int
    power: int
    consistency: int
    running: int
    fielding: int
    bowling: int
    pace: int
    spin: int
    deathBowling: int

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

def init_genai():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in the environment.")
    genai.configure(api_key=api_key)

def analyze_players(player_names: List[str]) -> Dict[str, Any]:
    """
    Sends a batch of player names to the Gemini API and asks for strict JSON schema output.
    Returns a dictionary mapping the original name to the parsed PlayerAIOuputSchema data.
    """
    init_genai()
    
    # We use gemini-3.6-flash for better speed and compatibility
    model = genai.GenerativeModel('gemini-3.6-flash', generation_config={"response_mime_type": "application/json"})
    
    prompt = f"""
    You are an expert cricket analyst. I am providing you with a list of cricket player names.
    For each player, identify their true cricket role and generate highly realistic 0-100 ratings based on their actual career statistics and playstyle.
    
    RULES:
    1. Roles allowed: "Batter", "Wicketkeeper Batter", "All-rounder", "Bowling All-rounder", "Fast Bowler", "Spin Bowler", "Unknown". NEVER default to Batter.
    2. Primary Skills allowed: "batting", "bowling", "all_round", "wicketkeeping".
    3. Ratings:
       - Fast Bowlers must have high bowling/pace, and low batting (unless they can bat).
       - Spin Bowlers must have high bowling/spin, and low pace.
       - Batters must have high batting/power/consistency, and low bowling.
       - Do NOT copy-paste generic ratings like 90 for everything.
       - If you don't know the player, use role="Unknown" and confidence="LOW".
    
    Return a JSON array of objects. Each object must have this exact structure:
    {{
      "name": "Original Player Name",
      "role": "Role string",
      "primarySkill": "primary skill string",
      "secondarySkill": "optional secondary skill string",
      "isWicketkeeper": boolean,
      "battingStyle": "Right Hand" or "Left Hand",
      "bowlingStyle": "Right Arm Fast" etc.,
      "ratings": {{
        "batting": int,
        "power": int,
        "consistency": int,
        "running": int,
        "fielding": int,
        "bowling": int,
        "pace": int,
        "spin": int,
        "deathBowling": int
      }},
      "confidence": "HIGH" or "LOW"
    }}
    
    PLAYERS TO ANALYZE:
    {json.dumps(player_names)}
    """
    
    response = model.generate_content(prompt)
    
    try:
        data = json.loads(response.text)
    except Exception as e:
        raise ValueError(f"Failed to parse LLM response as JSON: {response.text}")
        
    results = {}
    
    for item in data:
        try:
            parsed_player = PlayerAIOuputSchema(**item)
            results[parsed_player.name] = parsed_player
        except ValidationError as e:
            print(f"Validation failed for {item.get('name')}: {e}")
            continue
            
    return results

def validate_ratings(ai_data: PlayerAIOuputSchema) -> bool:
    """
    Validates the generated AI data logically.
    Returns True if valid, False if it warrants REVIEW_REQUIRED.
    """
    if ai_data.confidence.upper() == "LOW" or ai_data.role == "Unknown":
        return False
        
    r = ai_data.ratings
    
    if ai_data.role == "Fast Bowler":
        if r.batting >= r.bowling and r.bowling < 50: return False
        if r.pace < 60: return False
    elif ai_data.role == "Spin Bowler":
        if r.batting >= r.bowling and r.bowling < 50: return False
        if r.spin < 60: return False
    elif ai_data.role == "Batter":
        if r.bowling >= r.batting and r.batting < 50: return False
        if r.batting < 60: return False
    elif ai_data.role == "Wicketkeeper Batter":
        if not ai_data.isWicketkeeper: return False
    elif ai_data.role in ["All-rounder", "Bowling All-rounder"]:
        if r.batting < 40 or r.bowling < 40: return False
        
    return True
