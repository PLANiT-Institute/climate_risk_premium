#!/usr/bin/env python3
"""Upload model results from data/processed/*.csv to Supabase.

Usage:
    pip install supabase python-dotenv
    export SUPABASE_URL="https://xxx.supabase.co"
    export SUPABASE_SERVICE_KEY="eyJ..."
    python3 scripts/upload_results.py

Optionally set VERCEL_REVALIDATE_URL and REVALIDATE_SECRET to trigger ISR.
"""

import csv
import os
import subprocess
import sys
from pathlib import Path

try:
    from supabase import create_client
except ImportError:
    print("Install supabase: pip install supabase python-dotenv")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "processed"

BOOL_FIELDS = {"is_investment_grade", "is_distressed", "is_ebitda_negative", "verified"}
INT_FIELDS = {"rating_numeric", "notch_change", "year", "paper_id"}
TEXT_FIELDS = {"scenario", "overall_rating", "rating_rationale", "counterfactual_rating",
               "scenario_rating_new", "rating_migration", "display_name", "rating",
               "capacity_rating", "profitability_rating", "coverage_rating",
               "dscr_rating", "net_debt_leverage_rating", "equity_leverage_rating",
               "asset_leverage_rating", "authors", "title", "journal", "doi",
               "key_finding"}


def parse_value(key: str, value: str):
    if key in BOOL_FIELDS:
        return value.strip().lower() in ("true", "1", "yes")
    if key in TEXT_FIELDS:
        return value.strip()
    if key in INT_FIELDS:
        return int(float(value))
    try:
        return float(value)
    except (ValueError, TypeError):
        return value.strip()


def get_git_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=DATA_DIR.parent,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def read_csv(path: Path) -> list[dict]:
    with open(path) as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            if not any(v.strip() for v in row.values()):
                continue
            parsed = {k: parse_value(k, v) for k, v in row.items() if k}
            rows.append(parsed)
        return rows


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables.")
        sys.exit(1)

    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    git_hash = get_git_hash()

    # Create model run
    run = client.table("model_runs").insert({
        "git_hash": git_hash,
        "description": f"Automated upload from {git_hash}",
    }).execute()
    run_id = run.data[0]["id"]
    print(f"Created model run: {run_id} (git: {git_hash})")

    # Upload scenario_comparison.csv
    sc_path = DATA_DIR / "scenario_comparison.csv"
    if sc_path.exists():
        rows = read_csv(sc_path)
        for row in rows:
            row["run_id"] = run_id
        client.table("scenario_results").upsert(rows, on_conflict="run_id,scenario").execute()
        print(f"  scenario_results: {len(rows)} rows")

    # Upload cashflow files
    total_cf = 0
    for fpath in sorted(DATA_DIR.glob("cashflow_*.csv")):
        scenario = fpath.stem.replace("cashflow_", "")
        rows = read_csv(fpath)
        for row in rows:
            row["run_id"] = run_id
            row["scenario"] = scenario
        if rows:
            client.table("cashflow_timeseries").upsert(
                rows, on_conflict="run_id,scenario,year"
            ).execute()
            total_cf += len(rows)
    print(f"  cashflow_timeseries: {total_cf} rows")

    # Upload yearly_ratings.csv
    yr_path = DATA_DIR / "yearly_ratings.csv"
    if yr_path.exists():
        rows = read_csv(yr_path)
        for row in rows:
            row["run_id"] = run_id
        client.table("credit_rating_trajectories").upsert(
            rows, on_conflict="run_id,scenario,year"
        ).execute()
        print(f"  credit_rating_trajectories: {len(rows)} rows")

    # Trigger Vercel ISR revalidation
    revalidate_url = os.environ.get("VERCEL_REVALIDATE_URL")
    revalidate_secret = os.environ.get("REVALIDATE_SECRET")
    if revalidate_url and revalidate_secret:
        import urllib.request
        url = f"{revalidate_url}?secret={revalidate_secret}"
        req = urllib.request.Request(url, method="POST")
        try:
            resp = urllib.request.urlopen(req)
            print(f"  ISR revalidation: {resp.status}")
        except Exception as e:
            print(f"  ISR revalidation failed: {e}")

    print("Done.")


if __name__ == "__main__":
    main()
