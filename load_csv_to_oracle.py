"""
Simple CSV -> Oracle loader for the tables defined in build_tables.sql.

Usage examples:
  python load_csv_to_oracle.py --user scott --password tiger --dsn "localhost/orclpdb" --csv-dir data --truncate

Environment variables (used if flags are omitted):
  ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN

Notes:
  - Inserts run in the schema table order TEAM -> PLAYER -> COACH -> GAME -> GAME_STATS.
  - Set --truncate to clear tables before loading.
  - CSV column names must match those produced by load_api.py (TEAM.csv, PLAYER.csv, etc.).
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime
from typing import Iterable, List, Sequence, Tuple

import oracledb
import pandas as pd


TABLE_ORDER = [
    ("TEAM", ["TeamID", "TeamName", "City", "Conference", "Division"]),
    ("PLAYER", ["PlayerID", "Fname", "Lname", "Position", "TeamID"]),
    ("COACH", ["CoachID", "LName", "FName", "TeamID", "Role"]),
    ("GAME", ["GameID", "GameDate", "Week", "HomeTeamID", "AwayTeamID", "HomeTeamScore", "AwayTeamScore"]),
    ("GAME_STATS", ["GameID", "PlayerID", "Pass_yrd", "Rush_yrd", "Rec_yrd", "Touchdowns", "Tackles", "Interceptions"]),
]


def load_csv(csv_path: str, columns: Sequence[str]) -> List[Tuple]:
    df = pd.read_csv(csv_path)
    # Ensure all expected columns exist
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"{csv_path} missing columns {missing}")

    # Coerce NaN -> None and parse GameDate
    if "GameDate" in df.columns:
        df["GameDate"] = pd.to_datetime(df["GameDate"], errors="coerce")
    df = df.where(pd.notnull(df), None)
    rows: List[Tuple] = []
    for _, row in df.iterrows():
        values = []
        for col in columns:
            val = row[col]
            if isinstance(val, pd.Timestamp):
                val = val.to_pydatetime()
            values.append(val)
        rows.append(tuple(values))
    return rows


def truncate_tables(cursor: oracledb.Cursor, tables: Iterable[str]) -> None:
    for table in tables:
        cursor.execute(f"TRUNCATE TABLE {table}")


def insert_rows(cursor: oracledb.Cursor, table: str, columns: Sequence[str], rows: List[Tuple]) -> None:
    if not rows:
        return
    cols = ", ".join(columns)
    binds = ", ".join([f":{i+1}" for i in range(len(columns))])
    sql = f"INSERT INTO {table} ({cols}) VALUES ({binds})"
    cursor.executemany(sql, rows)


def main(args: argparse.Namespace) -> None:
    user = args.user or os.getenv("ORACLE_USER")
    password = args.password or os.getenv("ORACLE_PASSWORD")
    dsn = args.dsn or os.getenv("ORACLE_DSN")
    if not user or not password or not dsn:
        raise SystemExit("Missing credentials: set --user/--password/--dsn or ORACLE_USER/ORACLE_PASSWORD/ORACLE_DSN")

    conn = oracledb.connect(user=user, password=password, dsn=dsn)
    cursor = conn.cursor()

    if args.truncate:
        truncate_tables(cursor, [t for t, _ in TABLE_ORDER][::-1])  # child tables first when truncating
        conn.commit()

    player_ids = set()
    game_ids = set()

    for table, cols in TABLE_ORDER:
        csv_path = os.path.join(args.csv_dir, f"{table}.csv")
        print(f"[load] {table} from {csv_path}")
        rows = load_csv(csv_path, cols)

        # Drop orphan stats rows to avoid FK errors.
        if table == "GAME_STATS":
            filtered = []
            for r in rows:
                gid = r[0]
                pid = r[1]
                if gid in game_ids and pid in player_ids:
                    filtered.append(r)
            if len(filtered) != len(rows):
                print(f"[load] GAME_STATS: skipped {len(rows) - len(filtered)} rows missing parent GAME/PLAYER")
            rows = filtered

        insert_rows(cursor, table, cols, rows)
        print(f"[load] {table}: inserted {len(rows)} rows")
        if table == "PLAYER":
            player_ids = {r[0] for r in rows if r and r[0] is not None}
        if table == "GAME":
            game_ids = {r[0] for r in rows if r and r[0] is not None}

    conn.commit()
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load CSVs into Oracle tables.")
    parser.add_argument("--user", help="Oracle username (or ORACLE_USER env)")
    parser.add_argument("--password", help="Oracle password (or ORACLE_PASSWORD env)")
    parser.add_argument("--dsn", help="Oracle DSN, e.g. localhost/orclpdb (or ORACLE_DSN env)")
    parser.add_argument("--csv-dir", default="data", help="Directory containing TEAM.csv, PLAYER.csv, etc.")
    parser.add_argument("--truncate", action="store_true", help="Truncate tables before inserting")
    main(parser.parse_args())
