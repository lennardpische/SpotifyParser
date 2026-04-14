"""Interactive CLI to dismiss recommendations you don't want to see again.

Usage:
    python3 src/dismiss.py

For each recommendation: d=dismiss, Enter=keep, q=quit.
Dismissed track IDs are saved to dismissed.json and filtered from future runs.
"""
import sys
import os
import json
from datetime import datetime, timezone

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

DISMISSED_FILE = "dismissed.json"
RECS_FILE = "recommendations.csv"


def _load_dismissed(out_dir):
    path = os.path.join(out_dir, DISMISSED_FILE)
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_dismissed(entries, out_dir):
    path = os.path.join(out_dir, DISMISSED_FILE)
    try:
        with open(path, "w") as f:
            json.dump(entries, f, indent=2)
    except OSError as e:
        print(f"⚠️  Could not save dismissed.json: {e}")


def main():
    try:
        import pandas as pd
    except ImportError:
        print("pandas is required. Run: pip install pandas")
        sys.exit(1)

    out_dir = config.get_output_dir()
    recs_path = os.path.join(out_dir, RECS_FILE)

    if not os.path.exists(recs_path):
        print("No recommendations.csv found. Run parser.py first.")
        return

    try:
        df = pd.read_csv(recs_path)
    except Exception as e:
        print(f"Could not read recommendations.csv: {e}")
        return

    if df.empty:
        print("recommendations.csv is empty.")
        return

    dismissed = _load_dismissed(out_dir)
    dismissed_ids = {d["track_id"] for d in dismissed if d.get("track_id")}

    visible = df[~df["track_id"].isin(dismissed_ids)]
    if visible.empty:
        print("All current recommendations are already dismissed.")
        return

    print(f"\n{len(visible)} recommendations to review.")
    print("d=dismiss  Enter=keep  q=quit\n")

    new_dismissals = []
    total = len(visible)
    for i, (_, row) in enumerate(visible.iterrows(), 1):
        source = getattr(row, "source", "") or ""
        source_tag = f"  [{source}]" if source else ""
        print(f"[{i}/{total}] {row.track_name} — {row.artist}  (score: {row.similarity_score}{source_tag})")
        try:
            choice = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if choice == "q":
            break
        if choice == "d":
            new_dismissals.append({
                "track_id": row.track_id,
                "track_name": row.track_name,
                "artist": row.artist,
                "dismissed_at": datetime.now(timezone.utc).isoformat(),
            })
            print("  → Dismissed.")

    if new_dismissals:
        dismissed.extend(new_dismissals)
        _save_dismissed(dismissed, out_dir)
        print(f"\nDismissed {len(new_dismissals)} track(s). They won't appear in future recommendations.")
    else:
        print("\nNo changes.")


if __name__ == "__main__":
    main()
