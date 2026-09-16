import requests, sys, sqlite3
conn = sqlite3.connect('cricket.db')
cursor = conn.cursor()
cursor.execute("SELECT id FROM tournaments ORDER BY id DESC LIMIT 1;")
tourney_id = cursor.fetchone()[0]

data = requests.get(f"http://127.0.0.1:8001/api/tournaments/{tourney_id}/stats").json()
print("Top 3 Batters:")
for b in data['batting'][:3]:
    print(f" - {b['name']} (Runs: {b['runs']}, SR: {b['strike_rate']})")

print("\nTop 3 Bowlers:")
for b in data['bowling'][:3]:
    print(f" - {b['name']} (Wkts: {b['wickets']}, Overs: {b['overs']}, Econ: {b['economy']})")
    if float(b['overs']) > 4.0:
        print("   !!! ERROR: BOWLER BOWLED MORE THAN 4 OVERS !!!")
