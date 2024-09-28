# config.py
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get the OpenAI API key from the environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# SQLite Database file name
DB_FILE = 'conversation_history.db'
