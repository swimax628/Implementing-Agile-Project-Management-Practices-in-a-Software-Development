# config.py

import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv(dotenv_path=".env")

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Database Configuration
TAWOS_DB_URI = os.getenv("TAWOS_DB_URI")

# Validate Configuration
if not OPENAI_API_KEY:
    raise RuntimeError("OpenAI API key is missing. Please set the OPENAI_API_KEY environment variable.")

if not TAWOS_DB_URI:
    raise RuntimeError("TAWOS database URI is missing. Please set the TAWOS_DB_URI environment variable.")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s:%(message)s')
