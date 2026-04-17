"""Main entry: load config, auth, fetch recently played; accumulate history; generate recommendations."""
import sys
import os
import subprocess

# Ensure src is on path when run as script (e.g. python src/parser.py)
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import auth
import tracks
import recommendations


def _notify(message):
    """Send a macOS notification. No-op on non-macOS."""
    if sys.platform != "darwin":
        return
    try:
        subprocess.run(
            ["osascript", "-e", f'display notification "{message}" with title "SpotifyParser"'],
            timeout=5,
        )
    except Exception:
        pass


def main():
    print("\n--- 🟢 SCRIPT STARTED ---")
    if os.path.exists(config.DOTENV_PATH):
        print(f"--- 📂 Found .env file at: {config.DOTENV_PATH}")
    config.validate()

    try:
        sp = auth.get_spotify_client()
        user = sp.current_user()
        print(f"--- 👤 Logged in as: {user['display_name']} ---")
    except Exception as e:
        err = str(e)
        if "401" in err or "token" in err.lower() or "unauthorized" in err.lower():
            _notify("Spotify token expired — run: python3 src/parser.py to re-authenticate.")
            print("--- ❌ Token expired (HTTP 401). Re-run the script manually to re-authenticate. ---")
            sys.exit(1)
        raise

    out_dir = config.get_output_dir()

    print("\n--- 🕐 Fetching your Recently Played (listening history)... ---")
    recent_list = tracks.fetch_recently_played(sp, limit=50)
    tracks.warn_if_new_recently_played_list(recent_list, out_dir)
    listening_history = tracks.merge_recently_played_into_history(recent_list, out_dir)
    print(f"--- ✅ Listening history: {len(listening_history)} tracks (accumulated in listening_history.json) ---")

    print("\n--- 🔍 Fetching discovery tracks from Spotify... ---")
    seed_artist_ids = [r["artist_id"] for r in recent_list[:5] if r.get("artist_id")]
    history_ids = {t["track_id"] for t in listening_history if t.get("track_id")}
    market = user.get("country", "US")
    discovered = tracks.fetch_discovered_tracks(sp, seed_artist_ids, limit=100, market=market, history_ids=history_ids)
    tracks.save_discovered_tracks(discovered, out_dir)
    print(f"--- ✅ Discovery: {len(discovered)} candidate tracks saved to discovered_tracks.json ---")

    print("\n--- 🤖 Generating recommendations (sentence-transformer embeddings)... ---")
    recs = recommendations.generate_recommendations(out_dir, discovered=discovered)
    recs_path = recommendations.save_recommendations(recs, out_dir)
    if recs_path:
        print(f"--- 💾 Saved {len(recs)} recommendations to {recs_path} ---")
    else:
        print("--- ⚠️ No recommendations generated (not enough data yet). ---")


if __name__ == "__main__":
    main()
