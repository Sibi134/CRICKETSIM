import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.database import SessionLocal, engine
from app import models

models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

teams = [
    {"id": "CSK", "name": "Chennai Super Kings", "short_name": "CSK", "primary_color": "#FFFF00", "secondary_color": "#0000FF"},
    {"id": "MI", "name": "Mumbai Indians", "short_name": "MI", "primary_color": "#004BA0", "secondary_color": "#D1AB3E"},
    {"id": "RCB", "name": "Royal Challengers Bengaluru", "short_name": "RCB", "primary_color": "#EC1C24", "secondary_color": "#000000"},
    {"id": "KKR", "name": "Kolkata Knight Riders", "short_name": "KKR", "primary_color": "#3A225D", "secondary_color": "#B3A123"},
    {"id": "SRH", "name": "Sunrisers Hyderabad", "short_name": "SRH", "primary_color": "#F26522", "secondary_color": "#000000"},
    {"id": "DC", "name": "Delhi Capitals", "short_name": "DC", "primary_color": "#00008B", "secondary_color": "#FF0000"},
    {"id": "PBKS", "name": "Punjab Kings", "short_name": "PBKS", "primary_color": "#ED1B24", "secondary_color": "#D7CDBB"},
    {"id": "RR", "name": "Rajasthan Royals", "short_name": "RR", "primary_color": "#EA1A85", "secondary_color": "#001D48"},
    {"id": "LSG", "name": "Lucknow Super Giants", "short_name": "LSG", "primary_color": "#005087", "secondary_color": "#FF8200"},
    {"id": "GT", "name": "Gujarat Titans", "short_name": "GT", "primary_color": "#1B2133", "secondary_color": "#B3985A"},
]

for t in teams:
    existing = db.query(models.Team).filter(models.Team.id == t["id"]).first()
    if not existing:
        team_db = models.Team(
            id=t["id"],
            name=t["name"],
            short_name=t["short_name"],
            primary_color=t["primary_color"],
            secondary_color=t["secondary_color"]
        )
        db.add(team_db)

db.commit()
print("Teams seeded.")
