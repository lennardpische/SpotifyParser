# Next steps

- **Seed-based recs:** I’ll use `my_tracks.csv` `track_id` (and optionally artist) with [Spotify Get Recommendations](https://developer.spotify.com/documentation/web-api/reference/get-recommendations). No ML.
- **Audio features:** I’ll call [Get Track's Audio Features](https://developer.spotify.com/documentation/web-api/reference/get-audio-features) for my tracks and use the features as extra seeds or for similarity.
- **NLP / embeddings:** I’ll run sentence-transformers (e.g. `all-MiniLM-L6-v2`) on `track_name` + `artist` + `album` and use cosine similarity or k-NN for “similar tracks” in my data.
- **Sequence / transformer:** I’ll treat listening order (e.g. `played_at`) as a sequence, train a next-track or next-embedding model (PyTorch), and use predictions with Spotify’s API or a lookup.
- **Audio / CNN:** If I go beyond Spotify features, I’ll use librosa + spectrograms and a small CNN (e.g. ResNet) on audio or album art for an extra rec signal.
