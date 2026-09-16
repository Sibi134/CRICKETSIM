import requests

# 1. Import team 2 (since team 1 is already in DB)
team2 = {
  "team": {
    "id": "TEAM002",
    "name": "Mumbai Indians",
    "shortName": "MI",
    "primaryColor": "#004BA0",
    "secondaryColor": "#D1AB3E"
  },
  "players": []
}
# Just adding dummy players to pass validation
for i in range(12):
    role = "Batter" if i > 0 else "Wicketkeeper Batter"
    team2["players"].append({
        "id": f"MI_P{i}",
        "name": f"Player {i}",
        "nationality": "India",
        "role": role,
        "ratings": {"batting": 50, "power": 50, "consistency": 50, "running": 50, "fielding": 50, "bowling": 50, "pace": 50, "spin": 50, "deathBowling": 50}
    })
requests.post('http://127.0.0.1:8001/api/teams/import', json=team2)

# 2. Create tournament
res = requests.post('http://127.0.0.1:8001/api/tournaments', json={"name": "IPL 2026"})
if res.status_code != 200:
    print(res.text)
res.raise_for_status()
t_id = res.json()["id"]
print(f"Created tournament: {t_id}")

# 3. Generate schedule
res = requests.post(f'http://127.0.0.1:8001/api/tournaments/{t_id}/schedule/generate')
print(res.json())

# 4. Get matches
res = requests.get(f'http://127.0.0.1:8001/api/matches/tournament/{t_id}')
print(len(res.json()), "matches created")
