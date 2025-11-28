import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

MODEL_NAME = "gemini-2.5-flash"
CV_EXTENSIONS = ('.txt', '.pdf')

MAX_RETRIES = 4
INITIAL_BACKOFF = 1
