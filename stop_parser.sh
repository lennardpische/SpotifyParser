#!/bin/bash
launchctl unload ~/Library/LaunchAgents/com.spotifyparser.plist 2>/dev/null \
  && echo "SpotifyParser background job stopped." \
  || echo "SpotifyParser was not running."
