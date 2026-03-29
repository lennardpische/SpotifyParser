"""Main entry: load config, auth, fetch recently played; accumulate history; generate recommendations."""
import sys
import os

# Ensure src is on path when run as script (e.g. python src/parser.py)
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import auth
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

    out_dir = config.get_output_dir()

    print("\n--- 🕐 Fetching your Recently Played (listening history)... ---")
    recent_list = tracks.fetch_recently_played(sp, limit=50)
    tracks.warn_if_new_recently_played_list(recent_list, out_dir)
    listening_history = tracks.merge_recently_played_into_history(recent_list, out_dir)
    print(f"--- ✅ Listening history: {len(listening_history)} tracks (accumulated in listening_history.json) ---")

    print("\n--- 🤖 Generating recommendations (sentence-transformer embeddings)... ---")
    recs = recommendations.generate_recommendations(out_dir)
    recs_path = recommendations.save_recommendations(recs, out_dir)
    if recs_path:
        print(f"--- 💾 Saved {len(recs)} recommendations to {recs_path} ---")
    else:
        print("--- ⚠️ No recommendations generated (not enough data yet). ---")


if __name__ == "__main__":
    main()
