import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# App Configuration
class Config:
    # Supabase credentials checkout (secrets.toml has highest priority, then .env, then OS environment)
    SUPABASE_URL = None
    SUPABASE_KEY = None
    
    # Try loading from streamlit secrets
    try:
        if "SUPABASE_URL" in st.secrets:
            SUPABASE_URL = st.secrets["SUPABASE_URL"]
        if "SUPABASE_KEY" in st.secrets:
            SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    except Exception:
        # Ignore if st.secrets is not initialized (e.g. running unit tests directly)
        pass

    # If not in streamlit secrets, check env
    if not SUPABASE_URL:
        SUPABASE_URL = os.getenv("SUPABASE_URL")
    if not SUPABASE_KEY:
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # Flag to check if we can connect to Supabase
    IS_SUPABASE_CONFIGURED = bool(SUPABASE_URL and SUPABASE_KEY)
    
    # Session configurations
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    
    # SQLite Database Name (for fallback mode)
    SQLITE_DB_NAME = "bcc_portal.db"

    # Institute details
    INSTITUTE_NAME = "Phoenix Tech Academy"
    COURSE_NAME = "Basic Computer Course (BCC)"
