"""Load and validate environment and paths."""
import os
import sys
from dotenv import load_dotenv

# Paths
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(SRC_DIR, "..")
DOTENV_PATH = os.path.join(PROJECT_ROOT, ".env")

# Load .env
if os.path.exists(DOTENV_PATH):
    load_dotenv(DOTENV_PATH)
else:
    load_dotenv()

# Env vars (used by auth and main)
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

#Validation of the environment variables
def validate():
    """Exit if required env vars are missing."""
    if not CLIENT_ID or not CLIENT_SECRET:
        print("--- ❌ ERROR: Variables are MISSING. ---")
        print("    -> Check your .env file (SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET).")
        sys.exit(1)

#Getting the output directory
def get_output_dir():
    """Directory for CSVs (project root)."""
    return PROJECT_ROOT
