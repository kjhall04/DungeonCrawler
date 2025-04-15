from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

# Supabase URL and Key
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL or Key is not set or is invalid.")

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)