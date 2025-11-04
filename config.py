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

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
