"""Build the cricket match dataset used across the project.

Sources
-------
1. Cricsheet ball-by-ball archives (bulk download, https://cricsheet.org/downloads/).
2. CricAPI current-matches endpoint (REST API, requires CRICAPI_KEY).

Outputs (written to public/data/)
---------------------------------
cricsheet-matches-raw.csv     flattened match table before cleaning
cricsheet-matches-clean.csv   analysis-ready match table
cricapi-current-raw.csv       raw CricAPI snapshot
dataset-summary.json          row counts and class balance used by the website

Run:  python public/analysis/build_dataset.py
"""

from __future__ import annotations

import csv
import io
import json
import os
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


def clean_matches(raw: pd.DataFrame) -> pd.DataFrame:
    """Apply the documented cleaning rules and return the analysis table."""
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

    # 6. Drop innings that were cut far short of the scheduled allocation; a
    #    20-ball innings is a rain-affected fragment, not a contest.
    expected_balls = frame["scheduled_overs"].fillna(50) * 6
    frame = frame[frame["first_innings_balls"] >= 0.6 * expected_balls]

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
    frame["powerplay_run_rate"] = (
        frame["powerplay_runs"] / POWERPLAY_OVERS.get("ODI", 10.0)
    ).round(3)
    frame.loc[frame["match_type"] == "T20", "powerplay_run_rate"] = (
        frame.loc[frame["match_type"] == "T20", "powerplay_runs"] / 6.0
    ).round(3)
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
    records = payload.get("data") or []
    rows = []
    for record in records:
        teams = record.get("teams") or []
        score = record.get("score") or []
        rows.append({
            "match_name": record.get("name", ""),
            "status": record.get("status", ""),
            "venue": record.get("venue", ""),
            "team_1": teams[0] if len(teams) > 0 else "",
            "team_2": teams[1] if len(teams) > 1 else "",
            "date": record.get("date", ""),
            "match_type": record.get("matchType", ""),
            "innings_runs": sum(int(entry.get("r", 0) or 0) for entry in score),
            "innings_wickets": sum(int(entry.get("w", 0) or 0) for entry in score),
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

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
    clean = clean_matches(raw)
    clean.to_csv(DATA_DIR / "cricsheet-matches-clean.csv", index=False)
    print(f"   clean rows: {len(clean)}", flush=True)

    print("4. CricAPI snapshot", flush=True)
    snapshot = fetch_cricapi_snapshot()
    if snapshot is not None:
        snapshot.to_csv(DATA_DIR / "cricapi-current-raw.csv", index=False)
        print(f"   api rows: {len(snapshot)}", flush=True)

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
    }
    with open(DATA_DIR / "dataset-summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
