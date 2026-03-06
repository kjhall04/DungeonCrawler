import os
import json
import base64
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

BASE_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

def _decode_jwt_role(token: str | None) -> str | None:
    """Read the role claim from a Supabase JWT without verifying it."""
    if not token or token.count(".") < 2:
        return None

    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
        role = data.get("role")
        return role if isinstance(role, str) else None
    except Exception:
        return None


# Supabase URL and Key
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_SECRET_KEY or SUPABASE_ANON_KEY
SUPABASE_KEY_ROLE = _decode_jwt_role(SUPABASE_KEY)

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        f"Supabase URL or Key is not set. Expected SUPABASE_URL plus one of "
        f"SUPABASE_KEY, SUPABASE_SERVICE_ROLE_KEY, or SUPABASE_SECRET_KEY in {ENV_FILE}."
    )

# Create Supabase client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as exc:
    if str(exc) == "Invalid API key" and SUPABASE_KEY.startswith("sb_secret_"):
        raise ValueError(
            "The installed supabase Python client does not support sb_secret keys. "
            "Upgrade the 'supabase' package in api/requirements.txt and redeploy."
        ) from exc
    raise
