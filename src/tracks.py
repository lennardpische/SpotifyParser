"""Fetch recently played tracks and manage listening history."""
import json
import os
import config

LAST_RECENTLY_PLAYED_FILE = "last_recently_played.json"
LISTENING_HISTORY_FILE = "listening_history.json"
DISCOVERED_TRACKS_FILE = "discovered_tracks.json"


def _track_row(track, played_at=""):
    """Build a single track row dict."""
    artists_list = track.get("artists") or []
    artists = ", ".join(a.get("name", "") for a in artists_list)
    first_artist_id = artists_list[0].get("id", "") if artists_list else ""
    return {
        "track_name": track.get("name", ""),
        "artist": artists,
        "artist_id": first_artist_id,
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


def fetch_discovered_tracks(sp, seed_artist_ids, limit=20, market="US"):
    """Discover new tracks by browsing the catalog of your recently played artists.

    For each seed artist: fetch their albums/singles and sample tracks from those.
    This surfaces deeper cuts and recent releases you haven't heard yet.
    Returns list of track row dicts (no played_at — suggestions, not plays).
    """
    rows = []
    if not seed_artist_ids:
        return rows
    try:
        seen_track_ids = set()
        for aid in list(seed_artist_ids)[:5]:
            albums_resp = sp.artist_albums(aid, album_type="album,single", limit=5)
            for album in (albums_resp.get("items") or []):
                album_id = album.get("id")
                album_name = album.get("name", "")
                if not album_id:
                    continue
                tracks_resp = sp.album_tracks(album_id, limit=3)
                for track in (tracks_resp.get("items") or []):
                    if not track or track.get("type") != "track":
                        continue
                    tid = track.get("id")
                    if not tid or tid in seen_track_ids:
                        continue
                    seen_track_ids.add(tid)
                    # SimplifiedTrackObject has no album field; inject it
                    rows.append(_track_row({**track, "album": {"name": album_name}}))
                    if len(rows) >= limit:
                        break
                if len(rows) >= limit:
                    break
            if len(rows) >= limit:
                break
    except Exception as e:
        print(f"    ⚠️ Error fetching discovery tracks: {e}")
    return rows


def save_discovered_tracks(rows, out_dir=None):
    """Persist this run's discovery tracks to discovered_tracks.json."""
    out_dir = out_dir or config.get_output_dir()
    path = os.path.join(out_dir, DISCOVERED_TRACKS_FILE)
    try:
        with open(path, "w") as f:
            json.dump(rows, f, indent=0)
    except OSError:
        pass


def load_discovered_tracks(out_dir=None):
    """Load the most recently saved discovery tracks."""
    out_dir = out_dir or config.get_output_dir()
    path = os.path.join(out_dir, DISCOVERED_TRACKS_FILE)
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


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
