import requests, sys
LATEST_MATCH = sys.argv[1]
data = requests.get(f"http://127.0.0.1:8001/api/matches/{LATEST_MATCH}/scorecard").json()

def check_innings(inn, inn_name):
    if not inn: return
    batter_runs = sum(b['runs'] for b in inn['batting'])
    extras = inn['extras']['total']
    total_calc = batter_runs + extras
    total_actual = inn['total_runs']
    print(f"[{inn_name}] Batters: {batter_runs}, Extras: {extras} -> Calc: {total_calc} vs Actual: {total_actual}")
    if total_calc != total_actual:
        print("MISMATCH!")
    
    wickets_actual = inn['total_wickets']
    wickets_bat = sum(1 for b in inn['batting'] if b['is_out'])
    print(f"[{inn_name}] Wickets Actual: {wickets_actual}, Batting dismissals: {wickets_bat}")

check_innings(data.get('innings1'), 'Innings 1')
check_innings(data.get('innings2'), 'Innings 2')
