"""Fetch recently played tracks and manage listening history."""
import json
import os
import config

LAST_RECENTLY_PLAYED_FILE = "last_recently_played.json"
LISTENING_HISTORY_FILE = "listening_history.json"


def _track_row(track, played_at=""):
    """Build a single track row dict."""
    artists = ", ".join(a.get("name", "") for a in track.get("artists", []))
    return {
        "track_name": track.get("name", ""),
        "artist": artists,
        "track_id": track.get("id", ""),
        "album": track.get("album", {}).get("name", ""),
        "played_at": played_at,
    }


def fetch_recently_played(sp, limit=50):
    """Fetch user's recently played tracks (rolling window of ~50).
    Returns list of track row dicts with 'played_at' (ISO timestamp) set.
    """
    rows = []
    try:
        resp = sp.current_user_recently_played(limit=min(limit, 50))
        for item in resp.get("items", []):
            track = item.get("track")
            if not track or track.get("type") != "track":
                continue
            rows.append(_track_row(track, played_at=item.get("played_at", "")))
    except Exception as e:
        print(f"    ⚠️ Error fetching Recently Played: {e}")
    return rows


def warn_if_new_recently_played_list(recent_rows, out_dir=None):
    """Warn once when the 50 recently-played window has rotated to a new set."""
    out_dir = out_dir or config.get_output_dir()
    state_path = os.path.join(out_dir, LAST_RECENTLY_PLAYED_FILE)
    if len(recent_rows) < 50:
        return
    current_sig = [(r["track_id"], r.get("played_at", "")) for r in recent_rows]
    try:
        if os.path.exists(state_path):
            with open(state_path) as f:
                saved = json.load(f)
            if [tuple(x) for x in saved.get("signature", [])] == current_sig:
                return
        print("--- ⚠️ New list of 50 recently played songs (window has rotated). ---")
    finally:
        try:
            with open(state_path, "w") as f:
                json.dump({"signature": current_sig}, f)
        except OSError:
            pass


def _listening_history_path(out_dir):
    return os.path.abspath(os.path.join(out_dir or config.get_output_dir(), LISTENING_HISTORY_FILE))


def _load_listening_history(out_dir):
    path = _listening_history_path(out_dir)
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_listening_history(rows, out_dir):
    path = _listening_history_path(out_dir)
    try:
        with open(path, "w") as f:
            json.dump(rows, f, indent=0)
    except OSError:
        pass


def merge_recently_played_into_history(recent_rows, out_dir=None):
    """Merge this run's recently played into persistent history (distinct by track_id).
    New tracks are added; existing track_ids get played_at updated to latest.
    Returns the full accumulated list, newest first.
    """
    out_dir = out_dir or config.get_output_dir()
    existing = _load_listening_history(out_dir)
    by_id = {}
    for row in existing:
        tid = row.get("track_id")
        if tid:
            by_id[tid] = row
    added = 0
    for row in recent_rows:
        tid = row.get("track_id")
        if not tid:
            continue
        if tid not in by_id:
            added += 1
        by_id[tid] = row
    merged = sorted(by_id.values(), key=lambda r: r.get("played_at") or "", reverse=True)
    _save_listening_history(merged, out_dir)
    print(f"    Listening history: {len(existing)} existing + {added} new = {len(merged)} total")
    return merged
