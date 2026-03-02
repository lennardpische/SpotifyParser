# Next steps

- **Seed-based recs:** Use `my_tracks.csv` `track_id` (and optionally artist) with [Spotify Get Recommendations](https://developer.spotify.com/documentation/web-api/reference/get-recommendations). No ML.
- **Audio features:** Call [Get Track's Audio Features](https://developer.spotify.com/documentation/web-api/reference/get-audio-features) for your tracks; use features as extra seeds or for similarity.
- **NLP / embeddings:** Sentence-transformers (e.g. `all-MiniLM-L6-v2`) on `track_name` + `artist` + `album`; cosine similarity or k-NN for “similar tracks” in your data.
- **Sequence / transformer:** Treat listening order (e.g. `played_at`) as a sequence; train a next-track or next-embedding model (PyTorch); use predictions with Spotify’s API or a lookup.
- **Audio / CNN:** If you go beyond Spotify features: librosa + spectrograms, small CNN (e.g. ResNet) on audio or album art for an extra rec signal.
