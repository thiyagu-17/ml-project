"""Build the cricket match dataset used across the project.

Sources
-------
1. Cricsheet ball-by-ball archives (bulk download, https://cricsheet.org/downloads/).
2. CricAPI current-matches endpoint (REST API, requires CRICAPI_KEY).
3. Open-Meteo geocoding and historical-weather archive (REST API, no key).

Outputs (written to public/data/)
---------------------------------
cricsheet-matches-raw.csv     flattened match table before cleaning
cricsheet-matches-clean.csv   analysis-ready match table
cricapi-current-snapshot.csv  raw CricAPI response, one row per innings
cricapi-current-clean.csv     CricAPI innings cleaned to ODI/T20 with run rates
venue-weather.csv             match-day weather for the busiest host cities
dataset-summary.json          row counts and class balance used by the website

Run:  python public/analysis/build_dataset.py [--from-raw] [--skip-weather]

--from-raw      re-clean the committed raw CSV instead of downloading and
                re-parsing the archives (Cricsheet keeps adding matches, so a
                fresh download produces a larger raw file than the one on the site)
--skip-weather  do not call Open-Meteo; keep the committed venue-weather.csv
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import time
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import requests

PUBLIC_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = PUBLIC_DIR.parent
DATA_DIR = PUBLIC_DIR / "data"
CACHE_DIR = PROJECT_DIR / "data_cache"

CRICSHEET_ARCHIVES = {
    "odis_male": "https://cricsheet.org/downloads/odis_male_csv2.zip",
    "odis_female": "https://cricsheet.org/downloads/odis_female_csv2.zip",
    "t20s_male": "https://cricsheet.org/downloads/t20s_male_csv2.zip",
}

CRICAPI_URL = "https://api.cricapi.com/v1/currentMatches"
OPEN_METEO_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Weather is collected for every host city with at least this many cleaned
# matches. Cities whose name cannot be geocoded are skipped and reported.
WEATHER_MIN_MATCHES = 38
WEATHER_COLUMNS = ["city", "date", "latitude", "longitude",
                   "temp_max_c", "temp_min_c", "precipitation_mm"]

# Overs that count as the fielding-restriction powerplay in each format.
POWERPLAY_OVERS = {"ODI": 10.0, "T20": 6.0, "IT20": 6.0}


# --------------------------------------------------------------------------
# Cricsheet download and parsing
# --------------------------------------------------------------------------


def download_archives() -> dict[str, Path]:
    """Download each Cricsheet archive once into the local cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, url in CRICSHEET_ARCHIVES.items():
        target = CACHE_DIR / f"{name}.zip"
        if not target.exists():
            print(f"  downloading {name} ...", flush=True)
            response = requests.get(url, timeout=900, stream=True)
            response.raise_for_status()
            with open(target, "wb") as handle:
                for chunk in response.iter_content(chunk_size=1 << 20):
                    handle.write(chunk)
        paths[name] = target
    return paths


def parse_info_file(text: str) -> dict:
    """Turn one Cricsheet ``*_info.csv`` file into a flat dictionary.

    Repeated keys (team, umpire, player) are collected rather than overwritten
    so that no information is silently dropped at this stage.
    """
    single: dict[str, str] = {}
    teams: list[str] = []
    umpires: list[str] = []
    players: defaultdict[str, list[str]] = defaultdict(list)

    for row in csv.reader(io.StringIO(text)):
        if not row or row[0] != "info" or len(row) < 3:
            continue
        key, value = row[1], row[2]
        if key == "team":
            teams.append(value)
        elif key in {"umpire", "reserve_umpire", "tv_umpire"}:
            umpires.append(value)
        elif key == "player" and len(row) > 3:
            players[value].append(row[3])
        elif key in {"registry"}:
            continue
        elif key in {"target_overs", "target_runs", "winner_runs", "winner_wickets"} and len(row) > 3:
            # ``target_*`` rows carry the innings number in column 3.
            single[key] = row[3]
        else:
            single.setdefault(key, value)

    single["team_a"] = teams[0] if len(teams) > 0 else ""
    single["team_b"] = teams[1] if len(teams) > 1 else ""
    single["official_count"] = str(len(umpires))
    single["squad_size_a"] = str(len(players.get(single["team_a"], [])))
    single["squad_size_b"] = str(len(players.get(single["team_b"], [])))
    return single


def summarise_innings(frame: pd.DataFrame, powerplay_overs: float) -> dict[int, dict]:
    """Aggregate ball-by-ball rows into per-innings batting summaries."""
    summaries: dict[int, dict] = {}
    for innings_number in (1, 2):
        innings = frame[frame["innings"] == innings_number]
        if innings.empty:
            continue

        runs_off_bat = innings["runs_off_bat"]
        extras = innings["extras"]
        # A wide or a no-ball is re-bowled, so it is not a legal delivery.
        legal = innings["wides"].isna() & innings["noballs"].isna()
        legal_balls = int(legal.sum())
        powerplay = innings["ball"] < powerplay_overs

        summaries[innings_number] = {
            "batting_team": innings["batting_team"].iloc[0],
            "bowling_team": innings["bowling_team"].iloc[0],
            "runs": int(runs_off_bat.sum() + extras.sum()),
            "wickets": int(innings["player_dismissed"].notna().sum()),
            "balls": legal_balls,
            "overs": round(legal_balls / 6.0, 3),
            "fours": int((runs_off_bat == 4).sum()),
            "sixes": int((runs_off_bat == 6).sum()),
            "dot_balls": int(((runs_off_bat == 0) & (extras == 0) & legal).sum()),
            "extras": int(extras.sum()),
            "powerplay_runs": int(runs_off_bat[powerplay].sum() + extras[powerplay].sum()),
            "powerplay_wickets": int(innings.loc[powerplay, "player_dismissed"].notna().sum()),
        }
    return summaries


BALL_COLUMNS = [
    "match_id", "innings", "ball", "batting_team", "bowling_team",
    "runs_off_bat", "extras", "wides", "noballs", "player_dismissed",
]


def parse_archive(name: str, path: Path) -> list[dict]:
    """Read one archive and return one flat record per match."""
    records: list[dict] = []
    with zipfile.ZipFile(path) as archive:
        info_names = sorted(n for n in archive.namelist() if n.endswith("_info.csv"))
        print(f"  {name}: parsing {len(info_names)} matches", flush=True)

        for position, info_name in enumerate(info_names, start=1):
            if position % 500 == 0:
                print(f"    {position}/{len(info_names)}", flush=True)

            match_key = info_name[: -len("_info.csv")]
            ball_name = f"{match_key}.csv"
            if ball_name not in archive.namelist():
                continue

            info = parse_info_file(archive.read(info_name).decode("utf-8", "replace"))

            try:
                balls = pd.read_csv(
                    io.BytesIO(archive.read(ball_name)),
                    usecols=lambda c: c in BALL_COLUMNS,
                    low_memory=False,
                )
            except (ValueError, pd.errors.ParserError):
                continue
            if balls.empty or "innings" not in balls.columns:
                continue

            match_type = str(info.get("match_type", "")).upper()
            innings = summarise_innings(balls, POWERPLAY_OVERS.get(match_type, 10.0))
            if 1 not in innings:
                continue

            first, second = innings[1], innings.get(2, {})
            record = {
                "match_id": info.get("match_id", match_key),
                "source_archive": name,
                "match_type": info.get("match_type", ""),
                "gender": info.get("gender", ""),
                "team_type": info.get("team_type", ""),
                "season": info.get("season", ""),
                "date": info.get("date", ""),
                "event": info.get("event", ""),
                "venue": info.get("venue", ""),
                "city": info.get("city", ""),
                "team_a": info.get("team_a", ""),
                "team_b": info.get("team_b", ""),
                "toss_winner": info.get("toss_winner", ""),
                "toss_decision": info.get("toss_decision", ""),
                "winner": info.get("winner", ""),
                "outcome": info.get("outcome", ""),
                "method": info.get("method", ""),
                "winner_runs": info.get("winner_runs", ""),
                "winner_wickets": info.get("winner_wickets", ""),
                "player_of_match": info.get("player_of_match", ""),
                "scheduled_overs": info.get("overs", ""),
                "official_count": info.get("official_count", ""),
                "first_innings_team": first["batting_team"],
                "first_innings_runs": first["runs"],
                "first_innings_wickets": first["wickets"],
                "first_innings_balls": first["balls"],
                "first_innings_overs": first["overs"],
                "first_innings_fours": first["fours"],
                "first_innings_sixes": first["sixes"],
                "first_innings_dots": first["dot_balls"],
                "first_innings_extras": first["extras"],
                "powerplay_runs": first["powerplay_runs"],
                "powerplay_wickets": first["powerplay_wickets"],
                "second_innings_team": second.get("batting_team", ""),
                "second_innings_runs": second.get("runs", ""),
                "second_innings_wickets": second.get("wickets", ""),
                "second_innings_balls": second.get("balls", ""),
                "second_innings_overs": second.get("overs", ""),
            }
            records.append(record)
    return records


# --------------------------------------------------------------------------
# Cleaning
# --------------------------------------------------------------------------

TEAM_ALIASES = {
    "U.S.A.": "United States of America",
    "USA": "United States of America",
    "UAE": "United Arab Emirates",
    "P.N.G.": "Papua New Guinea",
    "PNG": "Papua New Guinea",
    "Cayman": "Cayman Islands",
    "Czech Rep.": "Czech Republic",
}


def canonical_venues(venues: pd.Series) -> pd.Series:
    """Collapse venue spellings that differ only by a trailing locality.

    Cricsheet records the same ground both as "Shere Bangla National Stadium"
    and as "Shere Bangla National Stadium, Mirpur". A name is only shortened
    when its prefix is itself used as a full venue name elsewhere in the file,
    so grounds that merely share a prefix (the several "County Ground" venues)
    are left alone.
    """
    known = set(venues.unique())
    mapping = {}
    for venue in known:
        prefix = venue.split(",")[0].strip()
        if prefix != venue and prefix in known:
            mapping[venue] = prefix
    return venues.replace(mapping)


def clean_matches(raw: pd.DataFrame, report: dict | None = None) -> pd.DataFrame:
    """Apply the documented cleaning rules and return the analysis table.

    If ``report`` is given, counts from individual rules are written into it.
    """
    frame = raw.copy()

    # 1. Normalise text columns and resolve known team-name aliases.
    text_columns = [
        "match_type", "gender", "team_type", "season", "event", "venue", "city",
        "team_a", "team_b", "toss_winner", "toss_decision", "winner", "outcome",
        "method", "first_innings_team", "second_innings_team", "player_of_match",
    ]
    for column in text_columns:
        frame[column] = frame[column].fillna("").astype(str).str.strip()
    for column in ["team_a", "team_b", "toss_winner", "winner", "first_innings_team", "second_innings_team"]:
        frame[column] = frame[column].replace(TEAM_ALIASES)

    frame["match_type"] = frame["match_type"].str.upper().replace({"IT20": "T20"})
    frame["venue"] = canonical_venues(frame["venue"])

    # 2. Parse the date and drop rows whose date cannot be recovered.
    frame["date"] = pd.to_datetime(frame["date"], format="mixed", errors="coerce")
    frame = frame[frame["date"].notna()].copy()
    frame["year"] = frame["date"].dt.year.astype(int)
    frame["month"] = frame["date"].dt.month.astype(int)
    frame["date"] = frame["date"].dt.strftime("%Y-%m-%d")

    # 3. Coerce every numeric column; a blank second innings means the chase
    #    never happened, which is information, so those rows are removed below
    #    rather than being filled with a fabricated zero.
    numeric_columns = [
        "first_innings_runs", "first_innings_wickets", "first_innings_balls",
        "first_innings_overs", "first_innings_fours", "first_innings_sixes",
        "first_innings_dots", "first_innings_extras", "powerplay_runs",
        "powerplay_wickets", "second_innings_runs", "second_innings_wickets",
        "second_innings_balls", "second_innings_overs", "scheduled_overs",
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    # 4. Remove matches that cannot support a result label: abandoned games,
    #    ties, and anything decided by Duckworth-Lewis, where the first-innings
    #    total no longer maps onto the target that was actually chased.
    frame = frame[frame["winner"] != ""]
    frame = frame[frame["outcome"] == ""]
    frame = frame[frame["method"] == ""]
    frame = frame[frame["second_innings_balls"].notna()]

    # 5. Remove structurally impossible rows.
    frame = frame[frame["first_innings_balls"] > 0]
    frame = frame[frame["first_innings_runs"] >= 0]
    frame = frame[frame["first_innings_wickets"].between(0, 10)]
    frame = frame[frame["second_innings_wickets"].between(0, 10)]
    frame = frame[frame["first_innings_team"] != ""]
    frame = frame[frame["second_innings_team"] != ""]

    # 6. Keep only first innings that reached at least 60 percent of the
    #    scheduled overs, so every total is compared with full-length innings.
    #    This removes interrupted fragments, and it also removes innings that
    #    ended early because the side was bowled out. Those are genuine results
    #    (almost all chased down), so how many were removed is reported.
    expected_balls = frame["scheduled_overs"].fillna(50) * 6
    short = frame["first_innings_balls"] < 0.6 * expected_balls
    if report is not None:
        report["short_innings_removed"] = int(short.sum())
        report["bowled_out_short_innings_removed"] = int(
            (short & (frame["first_innings_wickets"] == 10)).sum())
    frame = frame[~short]

    # 7. Remove exact duplicate fixtures.
    frame = frame.drop_duplicates(subset=["match_id"], keep="first")
    frame = frame.drop_duplicates(
        subset=["date", "team_a", "team_b", "first_innings_runs"], keep="first"
    )

    # 8. Fill the one genuinely optional text field.
    frame["city"] = frame["city"].replace("", np.nan)
    frame["city"] = frame["city"].fillna(frame["venue"].str.split(",").str[-1].str.strip())
    frame["city"] = frame["city"].replace("", "Unspecified")
    frame["event"] = frame["event"].replace("", "Bilateral series")
    frame["player_of_match"] = frame["player_of_match"].replace("", "Not awarded")

    # 9. Derive the analysis features.
    frame["first_innings_run_rate"] = (
        frame["first_innings_runs"] / (frame["first_innings_balls"] / 6.0)
    ).round(3)
    frame["second_innings_run_rate"] = (
        frame["second_innings_runs"] / (frame["second_innings_balls"] / 6.0)
    ).round(3)
    # The powerplay lasts 10 overs in an ODI and 6 in a T20, or less if the
    # side was bowled out before it ended.
    powerplay_length = np.where(frame["match_type"] == "T20",
                                POWERPLAY_OVERS["T20"], POWERPLAY_OVERS["ODI"])
    powerplay_length = np.minimum(powerplay_length, frame["first_innings_balls"] / 6.0)
    frame["powerplay_run_rate"] = (frame["powerplay_runs"] / powerplay_length).round(3)
    frame["boundary_runs"] = frame["first_innings_fours"] * 4 + frame["first_innings_sixes"] * 6
    frame["boundary_share"] = (frame["boundary_runs"] / frame["first_innings_runs"]).round(4)
    frame["dot_ball_share"] = (frame["first_innings_dots"] / frame["first_innings_balls"]).round(4)
    frame["extras_share"] = (frame["first_innings_extras"] / frame["first_innings_runs"]).round(4)

    # 10. Build the supervised label and the toss indicators.
    frame["toss_winner_batted"] = (frame["toss_winner"] == frame["first_innings_team"]).astype(int)
    frame["toss_winner_won_match"] = (frame["toss_winner"] == frame["winner"]).astype(int)
    frame["bat_first_won"] = (frame["winner"] == frame["first_innings_team"]).astype(int)
    frame["result_label"] = np.where(frame["bat_first_won"] == 1, "Defended", "Chased")

    # 11. Guard against division artefacts introduced in step 9.
    ratio_columns = ["boundary_share", "dot_ball_share", "extras_share",
                     "first_innings_run_rate", "second_innings_run_rate"]
    frame = frame.replace([np.inf, -np.inf], np.nan)
    frame = frame.dropna(subset=ratio_columns)
    frame = frame[frame["boundary_share"].between(0, 1)]
    frame = frame[frame["dot_ball_share"].between(0, 1)]

    ordered = [
        "match_id", "date", "year", "month", "season", "match_type", "gender",
        "event", "venue", "city", "team_a", "team_b", "toss_winner",
        "toss_decision", "toss_winner_batted", "first_innings_team",
        "second_innings_team", "winner", "result_label", "bat_first_won",
        "toss_winner_won_match", "first_innings_runs", "first_innings_wickets",
        "first_innings_overs", "first_innings_run_rate", "powerplay_runs",
        "powerplay_wickets", "powerplay_run_rate", "first_innings_fours",
        "first_innings_sixes", "boundary_runs", "boundary_share",
        "dot_ball_share", "first_innings_extras", "extras_share",
        "second_innings_runs", "second_innings_wickets", "second_innings_overs",
        "second_innings_run_rate", "player_of_match",
    ]
    return frame[ordered].sort_values("date").reset_index(drop=True)


# --------------------------------------------------------------------------
# REST API sources
# --------------------------------------------------------------------------


def fetch_cricapi_snapshot() -> pd.DataFrame | None:
    """Fetch the CricAPI current-matches endpoint when a key is available.

    The response is stored as returned, one row per innings, so nothing is lost
    before cleaning. Overs stay in cricket notation here (20.4 means 20 overs
    and 4 balls); ``clean_cricapi`` converts them.

    Example request:
        GET https://api.cricapi.com/v1/currentMatches?apikey=<KEY>&offset=0
    """
    api_key = os.environ.get("CRICAPI_KEY", "").strip()
    if not api_key:
        print("  CRICAPI_KEY not set - keeping the committed snapshot", flush=True)
        return None
    response = requests.get(CRICAPI_URL, params={"apikey": api_key, "offset": 0}, timeout=60)
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != "success":
        # The error text can echo the request, so it is not printed.
        print("  CricAPI returned no data - keeping the committed snapshot", flush=True)
        return None
    rows = []
    for record in payload.get("data") or []:
        teams = record.get("teams") or []
        base = {
            "match_id": record.get("id", ""),
            "match_name": record.get("name", ""),
            "status": record.get("status", ""),
            "venue": record.get("venue", ""),
            "date": record.get("date", ""),
            "match_type": record.get("matchType", ""),
            "team_1": teams[0] if len(teams) > 0 else "",
            "team_2": teams[1] if len(teams) > 1 else "",
        }
        for entry in record.get("score") or [{}]:
            rows.append({**base,
                         "inning": entry.get("inning", ""),
                         "runs": entry.get("r", ""),
                         "wickets": entry.get("w", ""),
                         "overs": entry.get("o", "")})
    return pd.DataFrame(rows)


def overs_to_balls(overs) -> float:
    """Convert cricket over notation (20.4 = 20 overs + 4 balls) into balls."""
    if pd.isna(overs):
        return np.nan
    whole = int(overs)
    extra = int(round((float(overs) - whole) * 10))
    if not 0 <= extra <= 5:
        return np.nan
    return float(whole * 6 + extra)


def infer_match_type(match_type, match_name) -> str:
    """Use the API's format, or read it from the match name when it is missing."""
    value = str(match_type or "").strip().upper()
    if value in {"ODI", "T20"}:
        return value
    name = str(match_name or "").upper()
    if re.search(r"\bODI\b", name):
        return "ODI"
    if re.search(r"\bT20", name):
        return "T20"
    return value


def resolve_batting_teams(frame: pd.DataFrame) -> pd.Series:
    """Name the batting side of each innings using the match's own team list.

    The API labels innings inconsistently: sometimes in lower case, and
    sometimes with both team names ("A,B Inning 1"). A label that matches one
    team is mapped to that team's proper spelling; a label naming both teams is
    resolved to whichever team has not already batted in that match.
    """
    labels = (frame["inning"].fillna("").astype(str)
              .str.replace(r"\s+Inning\s+\d+\s*$", "", regex=True).str.strip())
    resolved = pd.Series("", index=frame.index, dtype=object)
    for index, label in labels.items():
        for team in (frame.at[index, "team_1"], frame.at[index, "team_2"]):
            if isinstance(team, str) and label.lower() == team.strip().lower():
                resolved[index] = team.strip()
    for _, group in frame.groupby("match_id"):
        teams = {str(t).strip() for t in group[["team_1", "team_2"]].iloc[0] if isinstance(t, str)}
        known = set(resolved[group.index]) - {""}
        for index in group.index:
            if not resolved[index] and len(teams - known) == 1:
                resolved[index] = (teams - known).pop()
    return resolved


def clean_cricapi(raw: pd.DataFrame) -> pd.DataFrame:
    """Keep scored ODI and T20 innings and derive a correct run rate."""
    frame = raw.copy()
    frame["match_type"] = [infer_match_type(t, n)
                           for t, n in zip(frame["match_type"], frame["match_name"])]
    frame = frame[frame["match_type"].isin(["ODI", "T20"])].copy()
    for column in ["runs", "wickets", "overs"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["runs", "wickets", "overs"])
    frame["balls"] = frame["overs"].map(overs_to_balls)
    frame = frame[(frame["balls"] > 0) & frame["wickets"].between(0, 10) & (frame["runs"] >= 0)].copy()
    frame["batting_team"] = resolve_batting_teams(frame)
    frame = frame[frame["batting_team"] != ""]
    frame["overs_decimal"] = (frame["balls"] / 6.0).round(3)
    frame["run_rate"] = (frame["runs"] / (frame["balls"] / 6.0)).round(3)
    frame = frame.drop_duplicates(subset=["match_id", "inning"])
    columns = ["match_id", "match_name", "status", "venue", "date", "match_type",
               "batting_team", "runs", "wickets", "overs", "balls", "overs_decimal", "run_rate"]
    return frame[columns].reset_index(drop=True)


def fetch_weather(clean: pd.DataFrame, cache_path: Path) -> pd.DataFrame:
    """Daily weather on every match day in the busiest host cities.

    Rows already in ``cache_path`` are reused, so only new cities or new match
    dates are requested from the API.

    Example requests:
        GET https://geocoding-api.open-meteo.com/v1/search?name=Mumbai&count=1
        GET https://archive-api.open-meteo.com/v1/archive?latitude=19.07&longitude=72.87
            &start_date=2015-01-01&end_date=2015-12-31
            &daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=UTC
    """
    if cache_path.exists():
        cached = pd.read_csv(cache_path)
    else:
        cached = pd.DataFrame(columns=WEATHER_COLUMNS)
    counts = clean["city"].value_counts()
    cities = [city for city, count in counts.items() if count >= WEATHER_MIN_MATCHES]

    frames = [cached]
    for city in cities:
        needed = set(clean.loc[clean["city"] == city, "date"])
        have = set(cached.loc[cached["city"] == city, "date"])
        missing = sorted(needed - have)
        if not missing:
            continue

        known = cached.loc[cached["city"] == city, ["latitude", "longitude"]]
        if len(known):
            latitude, longitude = (float(v) for v in known.iloc[0])
        else:
            reply = requests.get(OPEN_METEO_GEOCODE_URL,
                                 params={"name": city, "count": 1, "format": "json"}, timeout=60)
            reply.raise_for_status()
            results = reply.json().get("results") or []
            if not results:
                print(f"    weather: no coordinates found for {city!r}, skipped", flush=True)
                continue
            latitude = round(float(results[0]["latitude"]), 3)
            longitude = round(float(results[0]["longitude"]), 3)

        reply = requests.get(OPEN_METEO_ARCHIVE_URL, params={
            "latitude": latitude, "longitude": longitude,
            "start_date": missing[0], "end_date": missing[-1],
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "UTC",
        }, timeout=180)
        reply.raise_for_status()
        daily = pd.DataFrame(reply.json().get("daily") or {})
        time.sleep(0.5)
        if daily.empty:
            continue
        daily = daily.rename(columns={"time": "date", "temperature_2m_max": "temp_max_c",
                                      "temperature_2m_min": "temp_min_c",
                                      "precipitation_sum": "precipitation_mm"})
        daily = daily[daily["date"].isin(missing)].assign(
            city=city, latitude=latitude, longitude=longitude)
        print(f"    weather: {city} +{len(daily)} match days", flush=True)
        frames.append(daily[WEATHER_COLUMNS])

    weather = pd.concat(frames, ignore_index=True)
    # Keep only match days still present in the cleaned table, and only
    # complete readings, so the file has no empty cells.
    keys = set(zip(clean["city"], clean["date"]))
    in_clean = [key in keys for key in zip(weather["city"], weather["date"])]
    weather = weather[in_clean]
    weather = weather[weather["city"].isin(cities)]
    weather = weather.dropna().drop_duplicates(subset=["city", "date"])
    return weather.sort_values(["city", "date"]).reset_index(drop=True)


# --------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the cricket match dataset.")
    parser.add_argument("--from-raw", action="store_true",
                        help="re-clean the committed raw CSV instead of re-downloading")
    parser.add_argument("--skip-weather", action="store_true",
                        help="keep the committed venue-weather.csv")
    args = parser.parse_args()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if args.from_raw:
        print("1-2. Reading the committed raw table", flush=True)
        raw = pd.read_csv(DATA_DIR / "cricsheet-matches-raw.csv", low_memory=False)
    else:
        print("1. Downloading Cricsheet archives", flush=True)
        archives = download_archives()

        print("2. Parsing ball-by-ball data", flush=True)
        records: list[dict] = []
        for name, path in archives.items():
            records.extend(parse_archive(name, path))
        raw = pd.DataFrame(records)
        raw.to_csv(DATA_DIR / "cricsheet-matches-raw.csv", index=False)
    print(f"   raw rows: {len(raw)}", flush=True)

    print("3. Cleaning", flush=True)
    cleaning_report: dict = {}
    clean = clean_matches(raw, cleaning_report)
    clean.to_csv(DATA_DIR / "cricsheet-matches-clean.csv", index=False)
    print(f"   clean rows: {len(clean)}", flush=True)

    print("4. CricAPI snapshot", flush=True)
    snapshot = fetch_cricapi_snapshot()
    snapshot_path = DATA_DIR / "cricapi-current-snapshot.csv"
    if snapshot is not None:
        snapshot.to_csv(snapshot_path, index=False)
        print(f"   api innings rows: {len(snapshot)}", flush=True)
    if snapshot_path.exists() and "inning" in pd.read_csv(snapshot_path, nrows=0).columns:
        api_clean = clean_cricapi(pd.read_csv(snapshot_path))
        api_clean.to_csv(DATA_DIR / "cricapi-current-clean.csv", index=False)
        print(f"   api innings after cleaning: {len(api_clean)}", flush=True)

    print("5. Open-Meteo weather", flush=True)
    if args.skip_weather:
        print("   skipped - keeping the committed venue-weather.csv", flush=True)
    else:
        weather = fetch_weather(clean, DATA_DIR / "venue-weather.csv")
        weather.to_csv(DATA_DIR / "venue-weather.csv", index=False)
        print(f"   weather rows: {len(weather)} across {weather['city'].nunique()} cities",
              flush=True)

    summary = {
        "raw_rows": int(len(raw)),
        "raw_columns": int(raw.shape[1]),
        "clean_rows": int(len(clean)),
        "clean_columns": int(clean.shape[1]),
        "rows_removed": int(len(raw) - len(clean)),
        "date_range": [clean["date"].min(), clean["date"].max()],
        "formats": clean["match_type"].value_counts().to_dict(),
        "genders": clean["gender"].value_counts().to_dict(),
        "venues": int(clean["venue"].nunique()),
        "teams": int(pd.concat([clean["team_a"], clean["team_b"]]).nunique()),
        "label_balance": clean["result_label"].value_counts().to_dict(),
        **cleaning_report,
    }
    with open(DATA_DIR / "dataset-summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
