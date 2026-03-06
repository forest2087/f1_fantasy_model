#!/usr/bin/env python3
"""Retry fetching missing 2025 constructor standings."""

import urllib.request
import json
import csv
import time
import io

BASE_URL = "https://api.jolpi.ca/ergast/f1"
DB_DIR = "f1db_csv"
REQUEST_DELAY = 2.0  # Longer delay to avoid rate limiting


def fetch_json(url):
    time.sleep(REQUEST_DELAY)
    print(f"  Fetching: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "F1FantasyModel/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


# Load constructor mapping
constructor_map = {}
with open(f"{DB_DIR}/constructors.csv") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        constructor_map[row[1]] = int(row[0])

# Load existing standings to get max ID and find missing rounds
with open(f"{DB_DIR}/constructor_standings.csv") as f:
    reader = csv.reader(f)
    header = next(reader)
    existing = list(reader)

max_cs_id = max(int(r[0]) for r in existing)

rounds_with_cs = set()
for r in existing:
    rid = int(r[1])
    if 1145 <= rid <= 1168:
        rounds_with_cs.add(rid - 1144)

missing_rounds = sorted(set(range(1, 25)) - rounds_with_cs)
print(f"Missing 2025 constructor standings for rounds: {missing_rounds}")

new_rows = []
for rnd in missing_rounds:
    race_id = 1144 + rnd
    try:
        data = fetch_json(f"{BASE_URL}/2025/{rnd}/constructorStandings.json")
        standings = data["MRData"]["StandingsTable"]["StandingsLists"]
        if not standings:
            print(f"  No standings for round {rnd}")
            continue
        for entry in standings[0].get("ConstructorStandings", []):
            max_cs_id += 1
            cref = entry["Constructor"]["constructorId"]
            cid = constructor_map.get(cref)
            if not cid:
                print(f"  WARNING: Unknown constructor {cref}")
                continue
            new_rows.append([
                str(max_cs_id), str(race_id), str(cid),
                entry.get("points", "0"), entry.get("position", "\\N"),
                entry.get("positionText", "\\N"), entry.get("wins", "0")
            ])
        print(f"  Round {rnd}: OK ({len(standings[0].get('ConstructorStandings', []))} entries)")
    except Exception as e:
        print(f"  Round {rnd}: FAILED ({e})")

if new_rows:
    existing.extend(new_rows)
    with open(f"{DB_DIR}/constructor_standings.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in existing:
            writer.writerow(row)
    print(f"\nAdded {len(new_rows)} constructor standings rows")
else:
    print("\nNo new rows to add")
