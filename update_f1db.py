#!/usr/bin/env python3
"""Fetch 2024 and 2025 F1 data from Jolpica API and update f1db CSVs."""

import urllib.request
import json
import csv
import os
import time
import io

BASE_URL = "https://api.jolpi.ca/ergast/f1"
DB_DIR = "f1db_csv"

# Rate limiting
REQUEST_DELAY = 0.5  # seconds between API calls


def fetch_json(url):
    """Fetch JSON from URL with rate limiting."""
    time.sleep(REQUEST_DELAY)
    print(f"  Fetching: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "F1FantasyModel/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def read_csv_file(filename):
    """Read a CSV file and return header + rows."""
    path = os.path.join(DB_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    header = rows[0] if rows else []
    data = rows[1:] if len(rows) > 1 else []
    # Filter out empty rows
    data = [r for r in data if any(cell.strip() for cell in r)]
    return header, data


def write_csv_file(filename, header, data):
    """Write header + data rows to CSV file."""
    path = os.path.join(DB_DIR, filename)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in data:
            writer.writerow(row)
    print(f"  Written {len(data)} rows to {filename}")


def load_mapping(filename, ref_col, id_col):
    """Load a mapping from string ref to numeric id."""
    header, data = read_csv_file(filename)
    ref_idx = header.index(ref_col)
    id_idx = header.index(id_col)
    mapping = {}
    for row in data:
        ref = row[ref_idx].strip('"')
        try:
            mapping[ref] = int(row[id_idx])
        except ValueError:
            pass
    return mapping


def load_status_mapping():
    """Load status text -> statusId mapping."""
    header, data = read_csv_file("status.csv")
    mapping = {}
    max_id = 0
    for row in data:
        sid = int(row[0])
        status = row[1].strip('"')
        mapping[status] = sid
        max_id = max(max_id, sid)
    return mapping, max_id


# ── Load existing mappings ──

print("Loading existing mappings...")
circuit_map = load_mapping("circuits.csv", "circuitRef", "circuitId")
driver_map = load_mapping("drivers.csv", "driverRef", "driverId")
constructor_map = load_mapping("constructors.csv", "constructorRef", "constructorId")
status_map, max_status_id = load_status_mapping()

# Load existing data to get max IDs
_, results_data = read_csv_file("results.csv")
max_result_id = max(int(r[0]) for r in results_data) if results_data else 0

_, quali_data = read_csv_file("qualifying.csv")
max_qualify_id = max(int(r[0]) for r in quali_data) if quali_data else 0

_, races_header_data = read_csv_file("races.csv")
races_header, races_data = read_csv_file("races.csv")
existing_race_ids = {int(r[0]) for r in races_data}
max_race_id = max(existing_race_ids) if existing_race_ids else 0

_, ds_data = read_csv_file("driver_standings.csv")
max_ds_id = max(int(r[0]) for r in ds_data) if ds_data else 0

_, cs_data = read_csv_file("constructor_standings.csv")
max_cs_id = max(int(r[0]) for r in cs_data) if cs_data else 0

_, cr_data = read_csv_file("constructor_results.csv")
max_cr_id = max(int(r[0]) for r in cr_data) if cr_data else 0

_, sprint_data = read_csv_file("sprint_results.csv")
max_sprint_id = max(int(r[0]) for r in sprint_data) if sprint_data else 0

drivers_header, drivers_data = read_csv_file("drivers.csv")
max_driver_id = max(int(r[0]) for r in drivers_data) if drivers_data else 0

constructors_header, constructors_data = read_csv_file("constructors.csv")
max_constructor_id = max(int(r[0]) for r in constructors_data) if constructors_data else 0

circuits_header, circuits_data = read_csv_file("circuits.csv")
max_circuit_id = max(int(r[0]) for r in circuits_data) if circuits_data else 0

seasons_header, seasons_data = read_csv_file("seasons.csv")
existing_seasons = {int(r[0]) for r in seasons_data}

print(f"  Max IDs: result={max_result_id}, qualify={max_qualify_id}, race={max_race_id}")
print(f"  Max IDs: driver={max_driver_id}, constructor={max_constructor_id}, circuit={max_circuit_id}")
print(f"  Max IDs: ds={max_ds_id}, cs={max_cs_id}, cr={max_cr_id}, sprint={max_sprint_id}")
print(f"  Drivers known: {len(driver_map)}, Constructors known: {len(constructor_map)}")


def get_or_create_driver(api_driver):
    """Get driverId for an API driver, creating new entry if needed."""
    global max_driver_id
    ref = api_driver["driverId"]
    if ref in driver_map:
        return driver_map[ref]
    max_driver_id += 1
    driver_map[ref] = max_driver_id
    num = api_driver.get("permanentNumber", "\\N")
    code = api_driver.get("code", "\\N")
    drivers_data.append([
        str(max_driver_id), ref, str(num), code,
        api_driver["givenName"], api_driver["familyName"],
        api_driver.get("dateOfBirth", "\\N"),
        api_driver.get("nationality", "\\N"),
        api_driver.get("url", "\\N")
    ])
    print(f"    New driver: {api_driver['givenName']} {api_driver['familyName']} (id={max_driver_id})")
    return max_driver_id


def get_or_create_constructor(api_constructor):
    """Get constructorId for an API constructor, creating new entry if needed."""
    global max_constructor_id
    ref = api_constructor["constructorId"]
    if ref in constructor_map:
        return constructor_map[ref]
    max_constructor_id += 1
    constructor_map[ref] = max_constructor_id
    constructors_data.append([
        str(max_constructor_id), ref,
        api_constructor["name"],
        api_constructor.get("nationality", "\\N"),
        api_constructor.get("url", "\\N")
    ])
    print(f"    New constructor: {api_constructor['name']} (id={max_constructor_id})")
    return max_constructor_id


def get_or_create_circuit(api_circuit):
    """Get circuitId for an API circuit, creating new entry if needed."""
    global max_circuit_id
    ref = api_circuit["circuitId"]
    if ref in circuit_map:
        return circuit_map[ref]
    max_circuit_id += 1
    circuit_map[ref] = max_circuit_id
    loc = api_circuit.get("Location", {})
    circuits_data.append([
        str(max_circuit_id), ref,
        api_circuit.get("circuitName", "\\N"),
        loc.get("locality", "\\N"),
        loc.get("country", "\\N"),
        loc.get("lat", "\\N"),
        loc.get("long", loc.get("lng", "\\N")),
        "0",
        api_circuit.get("url", "\\N")
    ])
    print(f"    New circuit: {api_circuit.get('circuitName', ref)} (id={max_circuit_id})")
    return max_circuit_id


def get_status_id(status_text):
    """Get statusId for a status string, creating new entry if needed."""
    global max_status_id
    if status_text in status_map:
        return status_map[status_text]
    max_status_id += 1
    status_map[status_text] = max_status_id
    print(f"    New status: {status_text} (id={max_status_id})")
    return max_status_id


def get_race_id(year, rnd):
    """Get raceId for a year/round. Uses existing IDs for 2024."""
    # 2024 races already in CSV: raceIds 1121-1144 for rounds 1-24
    if year == 2024:
        return 1120 + int(rnd)
    return None  # Will be assigned when creating new race entries


# ── Build mapping of year+round -> existing raceId ──
race_year_round_map = {}
for row in races_data:
    try:
        rid = int(row[0])
        yr = int(row[1])
        rnd = int(row[2])
        race_year_round_map[(yr, rnd)] = rid
    except (ValueError, IndexError):
        pass


# ── Process each year ──

new_results = []
new_qualifying = []
new_sprint = []
new_ds = []
new_cs = []
new_cr = []
new_races = []

for year in [2026]:  # 2024-2025 already in DB; add back when doing full refresh
    print(f"\n{'='*60}")
    print(f"Processing {year} season...")
    print(f"{'='*60}")

    # Fetch race schedule
    print(f"\nFetching {year} race schedule...")
    schedule = fetch_json(f"{BASE_URL}/{year}.json?limit=50")
    races = schedule["MRData"]["RaceTable"]["Races"]
    print(f"  Found {len(races)} races")

    # Add season if missing
    if year not in existing_seasons:
        seasons_data.append([str(year), f"https://en.wikipedia.org/wiki/{year}_Formula_One_World_Championship"])
        existing_seasons.add(year)
        print(f"  Added season {year}")

    # Process race schedule - assign raceIds
    year_race_ids = {}  # round -> raceId
    for race in races:
        if "round" not in race:
            print(f"  Skipping {race.get('raceName', 'unknown')} (no round - likely cancelled)")
            continue
        rnd = int(race["round"])
        circuit_id = get_or_create_circuit(race["Circuit"])

        if (year, rnd) in race_year_round_map:
            year_race_ids[rnd] = race_year_round_map[(year, rnd)]
        else:
            max_race_id += 1
            year_race_ids[rnd] = max_race_id

            # Build race row matching existing format
            race_time = race.get("time", "\\N")
            if race_time == "\\N":
                pass
            elif race_time.endswith("Z"):
                race_time = race_time[:-1]

            fp1_date = race.get("FirstPractice", {}).get("date", "\\N")
            fp1_time = race.get("FirstPractice", {}).get("time", "\\N")
            fp2_date = race.get("SecondPractice", {}).get("date", "\\N")
            fp2_time = race.get("SecondPractice", {}).get("time", "\\N")
            fp3_date = race.get("ThirdPractice", {}).get("date", "\\N")
            fp3_time = race.get("ThirdPractice", {}).get("time", "\\N")
            quali_date = race.get("Qualifying", {}).get("date", "\\N")
            quali_time = race.get("Qualifying", {}).get("time", "\\N")
            sprint_date = race.get("Sprint", {}).get("date", "\\N")
            sprint_time = race.get("Sprint", {}).get("time", "\\N")

            # Clean Z suffix from times
            for v in [fp1_time, fp2_time, fp3_time, quali_time, sprint_time]:
                if isinstance(v, str) and v.endswith("Z"):
                    v = v[:-1]

            url = race.get("url", "\\N")
            new_row = [
                str(max_race_id), str(year), str(rnd), str(circuit_id),
                race["raceName"], race["date"], race_time, url,
                fp1_date, fp1_time, fp2_date, fp2_time,
                fp3_date, fp3_time, quali_date, quali_time,
                sprint_date, sprint_time
            ]
            new_races.append(new_row)

    print(f"  Race IDs for {year}: {min(year_race_ids.values())}-{max(year_race_ids.values())}")

    # Fetch race results
    print(f"\nFetching {year} race results...")
    offset = 0
    all_race_results = []
    while True:
        data = fetch_json(f"{BASE_URL}/{year}/results.json?limit=100&offset={offset}")
        race_table = data["MRData"]["RaceTable"]["Races"]
        if not race_table:
            break
        all_race_results.extend(race_table)
        total = int(data["MRData"]["total"])
        offset += 100
        if offset >= total:
            break

    print(f"  Got results for {len(all_race_results)} races")

    for race in all_race_results:
        rnd = int(race["round"])
        race_id = year_race_ids.get(rnd)
        if not race_id:
            print(f"  WARNING: No raceId for round {rnd}")
            continue

        for result in race.get("Results", []):
            max_result_id += 1
            driver_id = get_or_create_driver(result["Driver"])
            constructor_id = get_or_create_constructor(result["Constructor"])
            status_id = get_status_id(result.get("status", "Unknown"))

            pos = result.get("position", "\\N")
            pos_text = result.get("positionText", "\\N")
            pos_order = result.get("positionOrder", pos if pos != "\\N" else "\\N")

            time_str = result.get("Time", {}).get("time", "\\N")
            millis = result.get("Time", {}).get("millis", "\\N")

            fl = result.get("FastestLap", {})
            fl_lap = fl.get("lap", "\\N")
            fl_rank = fl.get("rank", "\\N")
            fl_time = fl.get("Time", {}).get("time", "\\N")
            fl_speed = fl.get("AverageSpeed", {}).get("speed", "\\N")

            new_results.append([
                str(max_result_id), str(race_id), str(driver_id), str(constructor_id),
                result.get("number", "\\N"), result.get("grid", "\\N"),
                pos, pos_text, pos_order, result.get("points", "0"),
                result.get("laps", "0"), time_str, millis,
                fl_lap, fl_rank, fl_time, fl_speed, str(status_id)
            ])

    print(f"  Total new results: {len(new_results)}")

    # Fetch qualifying results
    print(f"\nFetching {year} qualifying results...")
    offset = 0
    all_quali = []
    while True:
        data = fetch_json(f"{BASE_URL}/{year}/qualifying.json?limit=100&offset={offset}")
        race_table = data["MRData"]["RaceTable"]["Races"]
        if not race_table:
            break
        all_quali.extend(race_table)
        total = int(data["MRData"]["total"])
        offset += 100
        if offset >= total:
            break

    print(f"  Got qualifying for {len(all_quali)} races")

    for race in all_quali:
        rnd = int(race["round"])
        race_id = year_race_ids.get(rnd)
        if not race_id:
            continue

        for result in race.get("QualifyingResults", []):
            max_qualify_id += 1
            driver_id = get_or_create_driver(result["Driver"])
            constructor_id = get_or_create_constructor(result["Constructor"])

            new_qualifying.append([
                str(max_qualify_id), str(race_id), str(driver_id), str(constructor_id),
                result.get("number", "\\N"), result.get("position", "\\N"),
                result.get("Q1", "\\N"), result.get("Q2", "\\N"), result.get("Q3", "\\N")
            ])

    # Fetch sprint results
    print(f"\nFetching {year} sprint results...")
    offset = 0
    all_sprint = []
    while True:
        data = fetch_json(f"{BASE_URL}/{year}/sprint.json?limit=100&offset={offset}")
        race_table = data["MRData"]["RaceTable"]["Races"]
        if not race_table:
            break
        all_sprint.extend(race_table)
        total = int(data["MRData"]["total"])
        offset += 100
        if offset >= total:
            break

    print(f"  Got sprint results for {len(all_sprint)} races")

    for race in all_sprint:
        rnd = int(race["round"])
        race_id = year_race_ids.get(rnd)
        if not race_id:
            continue

        for result in race.get("SprintResults", []):
            max_sprint_id += 1
            driver_id = get_or_create_driver(result["Driver"])
            constructor_id = get_or_create_constructor(result["Constructor"])
            status_id = get_status_id(result.get("status", "Unknown"))

            pos = result.get("position", "\\N")
            pos_text = result.get("positionText", "\\N")
            pos_order = result.get("positionOrder", pos if pos != "\\N" else "\\N")
            time_str = result.get("Time", {}).get("time", "\\N")
            millis = result.get("Time", {}).get("millis", "\\N")
            fl = result.get("FastestLap", {})
            fl_lap = fl.get("lap", "\\N")
            fl_time = fl.get("Time", {}).get("time", "\\N")

            new_sprint.append([
                str(max_sprint_id), str(race_id), str(driver_id), str(constructor_id),
                result.get("number", "\\N"), result.get("grid", "\\N"),
                pos, pos_text, pos_order, result.get("points", "0"),
                result.get("laps", "0"), time_str, millis,
                fl_lap, fl_time, str(status_id)
            ])

    # Fetch driver standings (after each round for the whole season)
    print(f"\nFetching {year} driver standings...")
    for rnd in sorted(year_race_ids.keys()):
        race_id = year_race_ids[rnd]
        try:
            data = fetch_json(f"{BASE_URL}/{year}/{rnd}/driverStandings.json")
            standings = data["MRData"]["StandingsTable"]["StandingsLists"]
            if not standings:
                continue
            for entry in standings[0].get("DriverStandings", []):
                max_ds_id += 1
                driver_id = get_or_create_driver(entry["Driver"])
                new_ds.append([
                    str(max_ds_id), str(race_id), str(driver_id),
                    entry.get("points", "0"), entry.get("position", "\\N"),
                    entry.get("positionText", "\\N"), entry.get("wins", "0")
                ])
        except Exception as e:
            print(f"    Standings error round {rnd}: {e}")
            continue

    # Fetch constructor standings
    print(f"\nFetching {year} constructor standings...")
    for rnd in sorted(year_race_ids.keys()):
        race_id = year_race_ids[rnd]
        try:
            data = fetch_json(f"{BASE_URL}/{year}/{rnd}/constructorStandings.json")
            standings = data["MRData"]["StandingsTable"]["StandingsLists"]
            if not standings:
                continue
            for entry in standings[0].get("ConstructorStandings", []):
                max_cs_id += 1
                constructor_id = get_or_create_constructor(entry["Constructor"])
                new_cs.append([
                    str(max_cs_id), str(race_id), str(constructor_id),
                    entry.get("points", "0"), entry.get("position", "\\N"),
                    entry.get("positionText", "\\N"), entry.get("wins", "0")
                ])
        except Exception as e:
            print(f"    Standings error round {rnd}: {e}")
            continue

    # Compute constructor results from race results
    print(f"\nComputing {year} constructor results...")
    cr_by_race_constructor = {}
    for row in new_results:
        race_id = int(row[1])
        constructor_id = int(row[3])
        points = float(row[9]) if row[9] != "\\N" else 0
        key = (race_id, constructor_id)
        cr_by_race_constructor[key] = cr_by_race_constructor.get(key, 0) + points

    for (race_id, constructor_id), points in sorted(cr_by_race_constructor.items()):
        # Only add if this race belongs to current year
        if race_id in year_race_ids.values():
            max_cr_id += 1
            new_cr.append([
                str(max_cr_id), str(race_id), str(constructor_id),
                str(points), "\\N"
            ])


# ── Write updated files ──

print(f"\n{'='*60}")
print("Writing updated CSV files...")
print(f"{'='*60}")

# Append new results
results_header, _ = read_csv_file("results.csv")
write_csv_file("results.csv", results_header, results_data + new_results)

# Append new qualifying
quali_header, _ = read_csv_file("qualifying.csv")
write_csv_file("qualifying.csv", quali_header, quali_data + new_qualifying)

# Append new sprint results
sprint_header, _ = read_csv_file("sprint_results.csv")
write_csv_file("sprint_results.csv", sprint_header, sprint_data + new_sprint)

# Append new driver standings
ds_header, _ = read_csv_file("driver_standings.csv")
write_csv_file("driver_standings.csv", ds_header, ds_data + new_ds)

# Append new constructor standings
cs_header, _ = read_csv_file("constructor_standings.csv")
write_csv_file("constructor_standings.csv", cs_header, cs_data + new_cs)

# Append new constructor results
cr_header, _ = read_csv_file("constructor_results.csv")
write_csv_file("constructor_results.csv", cr_header, cr_data + new_cr)

# Append new races
write_csv_file("races.csv", races_header, races_data + new_races)

# Write updated drivers
write_csv_file("drivers.csv", drivers_header, drivers_data)

# Write updated constructors
write_csv_file("constructors.csv", constructors_header, constructors_data)

# Write updated circuits
write_csv_file("circuits.csv", circuits_header, circuits_data)

# Write updated seasons
write_csv_file("seasons.csv", seasons_header, seasons_data)

# Write updated status (in case new statuses were added)
status_header = ["statusId", "status"]
status_data = [[str(v), k] for k, v in sorted(status_map.items(), key=lambda x: x[1])]
write_csv_file("status.csv", status_header, status_data)

print(f"\nDone! Summary:")
print(f"  New race results: {len(new_results)}")
print(f"  New qualifying: {len(new_qualifying)}")
print(f"  New sprint results: {len(new_sprint)}")
print(f"  New driver standings: {len(new_ds)}")
print(f"  New constructor standings: {len(new_cs)}")
print(f"  New constructor results: {len(new_cr)}")
print(f"  New races: {len(new_races)}")
print(f"  Drivers total: {len(drivers_data)}")
print(f"  Constructors total: {len(constructors_data)}")
