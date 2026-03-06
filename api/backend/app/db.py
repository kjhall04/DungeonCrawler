import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

BASE_DIR = Path(__file__).resolve().parents[3]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

# Supabase URL and Key
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = (
    os.getenv("SUPABASE_KEY")
    or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    or os.getenv("SUPABASE_SECRET_KEY")
)

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        f"Supabase URL or Key is not set. Expected SUPABASE_URL plus one of "
        f"SUPABASE_KEY, SUPABASE_SERVICE_ROLE_KEY, or SUPABASE_SECRET_KEY in {ENV_FILE}."
    )

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
