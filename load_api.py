"""
Lightweight loader for the Oracle schema in build_tables.sql.
Pulls the current season's data from ESPN public endpoints (no API key required)
and writes five CSVs shaped to TEAM / PLAYER / COACH / GAME / GAME_STATS.

Usage examples:
  python load_api.py --season 2025 --save
  python load_api.py --save --skip-game-stats
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime
import time
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd
import requests

ESPN_SITE = "https://site.api.espn.com/apis"
ESPN_CORE = "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl"
OUT_DIR = "data"

TEAM_COLUMNS = ["TeamID", "TeamName", "City", "Conference", "Division"]
PLAYER_COLUMNS = ["PlayerID", "Fname", "Lname", "Position", "TeamID"]
COACH_COLUMNS = ["CoachID", "LName", "FName", "TeamID", "Role"]
GAME_COLUMNS = ["GameID", "GameDate", "Week", "HomeTeamID", "AwayTeamID", "HomeTeamScore", "AwayTeamScore"]
GAME_STATS_COLUMNS = ["GameID", "PlayerID", "Pass_yrd", "Rush_yrd", "Rec_yrd", "Touchdowns", "Tackles", "Interceptions"]


def info(msg: str) -> None:
    print(f"[info] {msg}")


def fetch_json(url: str, timeout: int = 20) -> Optional[dict]:
    """Small wrapper around requests.get that returns parsed JSON or None."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        print(f"[warn] fetch failed {url}: {exc}")
        return None


def safe_int(value: Optional[str]) -> Optional[int]:
    try:
        return int(value)
    except Exception:
        return None


def split_name(full_name: str) -> Tuple[str, str]:
    parts = (full_name or "").strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[-1]


def conf_div_from_abbr(abbr: str) -> Tuple[str, str]:
    mapping = {
        "BUF": ("AFC", "E"), "MIA": ("AFC", "E"), "NE": ("AFC", "E"), "NYJ": ("AFC", "E"),
        "BAL": ("AFC", "N"), "CIN": ("AFC", "N"), "CLE": ("AFC", "N"), "PIT": ("AFC", "N"),
        "HOU": ("AFC", "S"), "IND": ("AFC", "S"), "JAX": ("AFC", "S"), "TEN": ("AFC", "S"),
        "DEN": ("AFC", "W"), "KC": ("AFC", "W"), "LAC": ("AFC", "W"), "LV": ("AFC", "W"),
        "DAL": ("NFC", "E"), "NYG": ("NFC", "E"), "PHI": ("NFC", "E"), "WAS": ("NFC", "E"), "WSH": ("NFC", "E"),
        "CHI": ("NFC", "N"), "DET": ("NFC", "N"), "GB": ("NFC", "N"), "MIN": ("NFC", "N"),
        "ATL": ("NFC", "S"), "CAR": ("NFC", "S"), "NO": ("NFC", "S"), "TB": ("NFC", "S"),
        "ARI": ("NFC", "W"), "LAR": ("NFC", "W"), "LA": ("NFC", "W"), "SF": ("NFC", "W"), "SEA": ("NFC", "W"),
    }
    return mapping.get(abbr.upper(), ("", ""))


def load_teams() -> pd.DataFrame:
    url = f"{ESPN_SITE}/site/v2/sports/football/nfl/teams"
    data = fetch_json(url)
    if not data:
        raise RuntimeError("Could not fetch teams")
    info("Fetched teams list")

    teams: List[dict] = []
    for sport in data.get("sports", []):
        for league in sport.get("leagues", []):
            for entry in league.get("teams", []):
                team = entry.get("team", {})
                abbr = (team.get("abbreviation") or "").upper()
                conference, division = conf_div_from_abbr(abbr)
                teams.append(
                    {
                        "TeamID": safe_int(team.get("id")),
                        "TeamName": (team.get("shortDisplayName") or team.get("displayName") or team.get("name") or "")[:15],
                        "City": (team.get("location") or team.get("displayName") or "").split()[0][:15],
                        "Conference": conference,
                        "Division": division,
                    }
                )
    return pd.DataFrame(teams, columns=TEAM_COLUMNS)


def load_roster(team_id: int) -> List[dict]:
    url = f"{ESPN_SITE}/common/v3/sports/football/nfl/teams/{team_id}/roster"
    data = fetch_json(url)
    if not data:
        return []

    players: List[dict] = []
    for group in data.get("positionGroups", []):
        for player in group.get("athletes", []):
            pid = safe_int(player.get("id"))
            if not pid:
                continue
            full_name = player.get("fullName") or player.get("displayName") or ""
            pos = player.get("position") or {}
            position = pos.get("abbreviation") if isinstance(pos, dict) else pos
            fname, lname = split_name(full_name)
            players.append(
                {
                    "PlayerID": pid,
                    "Fname": fname[:15],
                    "Lname": lname[:15],
                    "Position": (position or "").upper()[:4],
                    "TeamID": team_id,
                }
            )
    return players


def load_all_players(team_ids: Iterable[int]) -> pd.DataFrame:
    rows: List[dict] = []
    team_list = list(team_ids)
    total = len(team_list)
    for idx, tid in enumerate(team_list, start=1):
        info(f"Rosters: fetching team {tid} ({idx}/{total})")
        rows.extend(load_roster(int(tid)))
    df = pd.DataFrame(rows, columns=PLAYER_COLUMNS)
    df = df.drop_duplicates(subset=["PlayerID"])
    info(f"Built player roster with {len(df)} unique players")
    return df


def parse_id_from_ref(ref: Optional[str]) -> Optional[int]:
    if not ref:
        return None
    try:
        return int(ref.rstrip("/").split("/")[-1].split("?")[0])
    except Exception:
        return None


def load_coaches(team_ids: Iterable[int], season: int) -> pd.DataFrame:
    rows: List[dict] = []
    for tid in team_ids:
        coach_list_url = f"{ESPN_CORE}/seasons/{season}/teams/{tid}/coaches"
        listing = fetch_json(coach_list_url)
        if not listing:
            continue
        for item in listing.get("items", []):
            coach_ref = item.get("$ref")
            coach_data = fetch_json(coach_ref) if coach_ref else None
            if not coach_data:
                continue
            cid = safe_int(coach_data.get("id"))
            fname = (coach_data.get("firstName") or "")[:15]
            lname = (coach_data.get("lastName") or "")[:15]
            rows.append({"CoachID": cid, "LName": lname, "FName": fname, "TeamID": tid, "Role": "Head Coach"})
            break  # first coach is enough for this schema
    return pd.DataFrame(rows, columns=COACH_COLUMNS)


def fetch_score(score_ref: Optional[dict]) -> Optional[int]:
    if not score_ref or not isinstance(score_ref, dict):
        return None
    ref = score_ref.get("$ref")
    score_data = fetch_json(ref) if ref else None
    return safe_int(score_data.get("value")) if score_data else None


def load_games(season: int, max_weeks: int = 18) -> Tuple[pd.DataFrame, List[dict]]:
    rows: List[dict] = []
    stats_meta: List[dict] = []
    for week in range(1, max_weeks + 1):
        week_url = f"{ESPN_CORE}/seasons/{season}/types/2/weeks/{week}/events"
        info(f"Week {week}: fetching schedule ...")
        week_data = fetch_json(week_url)
        if not week_data or not week_data.get("items"):
            info("No events found; stopping week scan.")
            break
        info(f"Week {week}: found {len(week_data.get('items', []))} events")
        for item in week_data["items"]:
            event = fetch_json(item.get("$ref"))
            if not event:
                continue
            event_id = safe_int(event.get("id"))
            competitions = event.get("competitions") or []
            comp = competitions[0] if competitions else {}
            comp_id = safe_int(comp.get("id")) or event_id
            competitors = comp.get("competitors") or []
            home = next((c for c in competitors if c.get("homeAway") == "home"), None)
            away = next((c for c in competitors if c.get("homeAway") == "away"), None)
            if not home or not away:
                continue
            home_id = safe_int(home.get("id"))
            away_id = safe_int(away.get("id"))
            home_score = fetch_score(home.get("score"))
            away_score = fetch_score(away.get("score"))
            game_date = comp.get("date") or event.get("date")
            week_num = parse_id_from_ref(event.get("week")) or week
            rows.append(
                {
                    "GameID": event_id,
                    "GameDate": (game_date or "").split("T")[0],
                    "Week": week_num,
                    "HomeTeamID": home_id,
                    "AwayTeamID": away_id,
                    "HomeTeamScore": home_score,
                    "AwayTeamScore": away_score,
                }
            )
            stats_meta.append(
                {
                    "event_id": event_id,
                    "competition_id": comp_id,
                    "competitors": [home, away],
                    "status_ref": (comp.get("status") or {}).get("$ref"),
                }
            )
    return pd.DataFrame(rows, columns=GAME_COLUMNS), stats_meta


def stats_lookup(stats_obj: dict) -> dict:
    values = {}
    categories = stats_obj.get("splits", {}).get("categories", [])
    for cat in categories:
        for stat in cat.get("stats", []):
            values[stat.get("name")] = stat.get("value")
    return values


def load_game_stats(meta: List[dict]) -> pd.DataFrame:
    rows: List[dict] = []
    processed = 0
    for entry in meta:
        if not entry.get("event_id") or not entry.get("competition_id"):
            continue
        status = fetch_json(entry.get("status_ref")) if entry.get("status_ref") else None
        if status and status.get("type", {}).get("state") != "post":
            continue  # skip games that have not finished
        info(f"Game stats: processing event {entry.get('event_id')}")
        for comp in entry.get("competitors", []):
            team_id = safe_int(comp.get("id"))
            if not team_id:
                continue
            stats_url = f"{ESPN_CORE}/events/{entry['event_id']}/competitions/{entry['competition_id']}/competitors/{team_id}/statistics/0"
            stat_block = fetch_json(stats_url)
            if not stat_block:
                continue
            athlete_refs = []
            for cat in stat_block.get("splits", {}).get("categories", []):
                for ath in cat.get("athletes", []):
                    stat_ref = (ath.get("statistics") or {}).get("$ref")
                    athlete_ref = (ath.get("athlete") or {}).get("$ref")
                    athlete_id = parse_id_from_ref(athlete_ref)
                    if stat_ref and athlete_id:
                        athlete_refs.append((athlete_id, stat_ref))
            seen = set()
            for athlete_id, stat_ref in athlete_refs:
                if (entry["event_id"], athlete_id) in seen:
                    continue
                seen.add((entry["event_id"], athlete_id))
                detail = fetch_json(stat_ref)
                if not detail:
                    continue
                lookup = stats_lookup(detail)
                pass_yrd = lookup.get("passingYards") or lookup.get("netPassingYards") or 0
                rush_yrd = lookup.get("rushingYards") or 0
                rec_yrd = lookup.get("receivingYards") or 0
                td = (
                    (lookup.get("passingTouchdowns") or 0)
                    + (lookup.get("rushingTouchdowns") or 0)
                    + (lookup.get("receivingTouchdowns") or 0)
                )
                tackles = lookup.get("totalTackles") or lookup.get("tackles") or 0
                interceptions = lookup.get("interceptions") or 0
                rows.append(
                    {
                        "GameID": entry["event_id"],
                        "PlayerID": athlete_id,
                        "Pass_yrd": pass_yrd,
                        "Rush_yrd": rush_yrd,
                        "Rec_yrd": rec_yrd,
                        "Touchdowns": td,
                        "Tackles": tackles,
                        "Interceptions": interceptions,
                    }
                )
                processed += 1
                if processed % 50 == 0:
                    info(f"Game stats rows built: {processed}")
    return pd.DataFrame(rows, columns=GAME_STATS_COLUMNS)


def save_frames(frames: Dict[str, pd.DataFrame], out_dir: str = OUT_DIR) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for name, frame in frames.items():
        path = os.path.join(out_dir, f"{name}.csv")
        frame.to_csv(path, index=False)
        print(f"wrote {name} -> {path} ({len(frame)} rows)")


def main(season: Optional[int], save: bool, skip_game_stats: bool, max_weeks: int) -> Dict[str, pd.DataFrame]:
    season = int(season or datetime.now().year)
    start = time.time()
    info(f"Loading season {season} ...")

    teams = load_teams()
    players = load_all_players(teams["TeamID"].dropna().tolist())
    coaches = load_coaches(teams["TeamID"].dropna().tolist(), season)
    games, stats_meta = load_games(season, max_weeks=max_weeks)
    game_stats = pd.DataFrame(columns=GAME_STATS_COLUMNS)
    if not skip_game_stats:
        game_stats = load_game_stats(stats_meta)

    # Drop players who never recorded a stat in the fetched games to avoid bench-only rows.
    if not game_stats.empty:
        used_ids = set(game_stats["PlayerID"].unique())
        before = len(players)
        players = players[players["PlayerID"].isin(used_ids)]
        info(f"Pruned players with no stats: {before} -> {len(players)}")

    frames = {
        "TEAM": teams,
        "PLAYER": players,
        "COACH": coaches,
        "GAME": games,
        "GAME_STATS": game_stats,
    }

    if save:
        save_frames(frames, OUT_DIR)

    elapsed = time.time() - start
    info(f"Rows -> TEAM:{len(teams)} PLAYER:{len(players)} COACH:{len(coaches)} GAME:{len(games)} GAME_STATS:{len(game_stats)}")
    info(f"Done in {elapsed:.1f}s")
    return frames


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch current NFL season data into CSVs for Oracle demo tables.")
    parser.add_argument("--season", type=int, help="Season year (defaults to current year)")
    parser.add_argument("--save", action="store_true", help="Write CSVs into ./data")
    parser.add_argument("--skip-game-stats", action="store_true", help="Skip per-player game stats (faster)")
    parser.add_argument("--max-weeks", type=int, default=18, help="Limit weeks scanned for schedule (default 18)")
    args = parser.parse_args()

    main(season=args.season, save=args.save, skip_game_stats=args.skip_game_stats, max_weeks=args.max_weeks)

