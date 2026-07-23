"""
Configuration Module

Loads environment settings for the Streamlit frontend.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BACKEND_API_URL = os.getenv(
    "BACKEND_API_URL",
    "http://localhost:8000"
)