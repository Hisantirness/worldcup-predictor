import os
from dotenv import load_dotenv

load_dotenv()

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
API_FOOTBALL_URL = "https://v3.football.api-sports.io"
FOOTBALL_DATA_KEY = os.getenv("FOOTBALL_DATA_KEY") or os.getenv("FOOTBALL_DATA_API_KEY", "")
FOOTBALL_DATA_URL = "https://api.football-data.org/v4"
