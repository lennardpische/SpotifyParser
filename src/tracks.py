"""Fetch playlist tracks and liked songs from Spotify."""
import json
import os
import config

LAST_RECENTLY_PLAYED_FILE = "last_recently_played.json"
LISTENING_HISTORY_FILE = "listening_history.json"


def _track_row(playlist_name, playlist_id, track, played_at=""):
    """Build a single track row dict. played_at is optional (for listening history)."""
    artists = ", ".join(a.get("name", "") for a in track.get("artists", []))
    return {
        "playlist_name": playlist_name,
        "playlist_id": playlist_id,
        "track_name": track.get("name", ""),
        "artist": artists,
        "track_id": track.get("id", ""),
        "album": track.get("album", {}).get("name", ""),
        "played_at": played_at,
    }


def fetch_playlist_tracks(sp, playlists):
    """Fetch all tracks from the given playlists. Returns list of track row dicts."""
    all_tracks = []
    limit = 50
    for pl in playlists:
        pl_id, pl_name, pl_count = pl["id"], pl["name"], pl["tracks"]
        if pl_id == "No ID" or pl_count == 0:
            continue
        offset = 0
        while offset < pl_count:
            try:
                resp = sp._get(
                    f"playlists/{pl_id}/items",
                    limit=limit,
                    offset=offset,
                    additional_types="track",
                )
                for entry in resp.get("items", []):
                    track = entry.get("item") or entry.get("track")
                    if not track or track.get("type") != "track":
                        continue
                    all_tracks.append(_track_row(pl_name, pl_id, track, played_at=""))
                offset += len(resp.get("items", []))
                if not resp.get("next"):
                    break
            except Exception as e:
                print(f"    ⚠️ Error fetching {pl_name}: {e}")
                break
    return all_tracks


def fetch_liked_tracks(sp):
    """Fetch user's saved (liked) tracks. Returns list of track row dicts."""
    tracks = []
    offset = 0
    limit = 50
    while True:
        try:
            resp = sp.current_user_saved_tracks(limit=limit, offset=offset)
            items = resp.get("items", [])
            if not items:
                break
            for entry in items:
                track = entry.get("track")
                if not track or track.get("type") != "track":
                    continue
                tracks.append(_track_row("Liked Songs", "liked", track, played_at=""))
            offset += len(items)
            if not resp.get("next"):
                break
        except Exception as e:
            print(f"    ⚠️ Error fetching Liked Songs: {e}")
            break
    return tracks


def fetch_recently_played(sp, limit=50):
    """Fetch user's recently played tracks (listening history window).
    Spotify only exposes a rolling window (~last 50 plays), not full history.
    Returns list of track row dicts with 'played_at' (ISO timestamp) set.
    """
    rows = []
    try:
        resp = sp.current_user_recently_played(limit=min(limit, 50))
        for item in resp.get("items", []):
            track = item.get("track")
            if not track or track.get("type") != "track":
                continue
            played_at = item.get("played_at", "")  # ISO 8601
            rows.append(_track_row("Recently Played", "recently_played", track, played_at=played_at))
    except Exception as e:
        print(f"    ⚠️ Error fetching Recently Played: {e}")
    return rows


def warn_if_new_recently_played_list(recent_rows, out_dir=None):
    """Warn once when the 50 recently-played window has rotated to a new set.
    Persists the last seen list and compares on next run.
    """
    out_dir = out_dir or config.get_output_dir()
    state_path = os.path.join(out_dir, LAST_RECENTLY_PLAYED_FILE)
    if len(recent_rows) < 50:
        return
    # Signature: ordered list of (track_id, played_at) for the 50
    current_sig = [(r["track_id"], r.get("played_at", "")) for r in recent_rows]
    try:
        if os.path.exists(state_path):
            with open(state_path) as f:
                saved = json.load(f)
            saved_sig = [tuple(x) for x in saved.get("signature", [])]
            if saved_sig == current_sig:
                return
        # New list of 50 (first run or window rotated)
        print("--- ⚠️ New list of 50 recently played songs (window has rotated). ---")
    finally:
        try:
            with open(state_path, "w") as f:
                json.dump({"signature": current_sig}, f)
        except OSError:
            pass


def _load_listening_history(out_dir):
    """Load accumulated listening history from disk. Returns list of track row dicts."""
    path = os.path.join(out_dir, LISTENING_HISTORY_FILE)
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_listening_history(rows, out_dir):
    """Persist accumulated listening history to disk."""
    path = os.path.join(out_dir, LISTENING_HISTORY_FILE)
    try:
        with open(path, "w") as f:
            json.dump(rows, f, indent=0)
    except OSError:
        pass


def merge_recently_played_into_history(recent_rows, out_dir=None):
    """Merge this run's recently played into persistent history (distinct by track_id).
    New tracks are appended; existing track_ids get played_at updated to latest.
    Returns the full accumulated list for use in my_tracks.csv.
    """
    out_dir = out_dir or config.get_output_dir()
    # keyed by track_id -> full row (keep latest played_at)
    by_id = {}
    for row in _load_listening_history(out_dir):
        tid = row.get("track_id")
        if tid:
            by_id[tid] = row
    for row in recent_rows:
        tid = row.get("track_id")
        if not tid:
            continue
        # New or update: keep this row (newer played_at if we're seeing it again)
        by_id[tid] = row
    merged = list(by_id.values())
    _save_listening_history(merged, out_dir)
    return merged


def save_tracks_csv(tracks, out_dir=None):
    """Save track rows to my_tracks.csv. Returns path or None if no tracks."""
    import pandas as pd
    out_dir = out_dir or config.get_output_dir()
    if not tracks:
        return None
    path = os.path.join(out_dir, "my_tracks.csv")
    pd.DataFrame(tracks).to_csv(path, index=False)
    return path
