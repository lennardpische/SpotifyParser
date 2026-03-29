"""Main entry: load config, auth, fetch playlists and tracks; save library to CSV, listening history to JSON."""
import sys
import os

# Ensure src is on path when run as script (e.g. python src/parser.py)
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import auth
import playlists
import tracks
import recommendations


def main():
    print("\n--- 🟢 SCRIPT STARTED ---")
    if os.path.exists(config.DOTENV_PATH):
        print(f"--- 📂 Found .env file at: {config.DOTENV_PATH}")
    config.validate()

    sp = auth.get_spotify_client()
    user = sp.current_user()
    print(f"--- 👤 Logged in as: {user['display_name']} ---")

    print("--- 📥 Fetching Your Playlists... ---")
    playlists_list = playlists.fetch_playlists(sp)
    print(f"--- ✅ Found {len(playlists_list)} playlists ---")
    out_dir = config.get_output_dir()
    playlists_path = playlists.save_playlists_csv(playlists_list, out_dir)
    print(f"\n--- 💾 Saved to {playlists_path} ---")

    print("\n--- 📀 Fetching tracks from your playlists... ---")
    playlist_track_list = tracks.fetch_playlist_tracks(sp, playlists_list)
    print("\n--- 🎵 Fetching your Liked Songs... ---")
    liked_list = tracks.fetch_liked_tracks(sp)
    print("\n--- 🕐 Fetching your Recently Played (listening history)... ---")
    recent_list = tracks.fetch_recently_played(sp, limit=50)
    tracks.warn_if_new_recently_played_list(recent_list, out_dir)
    # Merge into persistent history (distinct by track_id)
    listening_history = tracks.merge_recently_played_into_history(recent_list, out_dir)
    print(f"--- ✅ Listening history: {len(listening_history)} tracks (accumulated in listening_history.json) ---")

    # CSV: playlists + liked only (no recently played)
    library_tracks = playlist_track_list + liked_list
    csv_path = tracks.save_tracks_csv(library_tracks, out_dir)
    if csv_path:
        print(f"--- 💾 Saved to {csv_path} (playlists + liked songs only) ---")
    else:
        print("--- ⚠️ No library tracks to save. ---")

    print("\n--- 🤖 Generating recommendations (sentence-transformer embeddings)... ---")
    recs = recommendations.generate_recommendations(out_dir)
    recs_path = recommendations.save_recommendations(recs, out_dir)
    if recs_path:
        print(f"--- 💾 Saved {len(recs)} recommendations to {recs_path} ---")
    else:
        print("--- ⚠️ No recommendations generated (not enough data yet). ---")


if __name__ == "__main__":
    main()
