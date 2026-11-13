import os
from pathlib import Path

os.environ["DISCOVERY_MODE"] = "live"
os.environ["AI_PROVIDER"] = "gemini"
os.environ["STORAGE_BACKEND"] = "local"
os.environ["GEMINI_API_KEY"] = ""
os.environ["DATA_DIR"] = str(Path(__file__).resolve().parent / "_testdata")

from app.config import get_settings

get_settings.cache_clear()