import os
import json
import datetime
from firebase_admin import credentials, firestore, initialize_app
from dotenv import load_dotenv

load_dotenv()

firebase_config_str = os.getenv("FIREBASE_CONFIG")

if not firebase_config_str:
    raise RuntimeError("Brak zmiennej środowiskowej FIREBASE_CONFIG")

try:
    firebase_config = json.loads(firebase_config_str)
except json.JSONDecodeError as e:
    raise RuntimeError(f"Błąd parsowania konfiguracji Firebase: {e}")

cred = credentials.Certificate(firebase_config)
initialize_app(cred)
db = firestore.client()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
try:
    allowed_origins_parsed = json.loads(allowed_origins_str)
    if isinstance(allowed_origins_parsed, dict):
        ALLOWED_ORIGINS = list(allowed_origins_parsed.values()) if allowed_origins_parsed else []
    elif isinstance(allowed_origins_parsed, list):
        ALLOWED_ORIGINS = allowed_origins_parsed
    else:
        ALLOWED_ORIGINS = [allowed_origins_parsed]
except json.JSONDecodeError:
    if allowed_origins_str.startswith("{") and allowed_origins_str.endswith("}"):
        clean_str = allowed_origins_str.strip("{}").strip('"\'')
        ALLOWED_ORIGINS = [clean_str] if clean_str else []
    else:
        ALLOWED_ORIGINS = [s.strip() for s in allowed_origins_str.split(",")]
