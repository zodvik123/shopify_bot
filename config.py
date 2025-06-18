import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('API_ID', '123456'))
API_HASH = os.getenv('API_HASH', 'demo_hash')
BOT_TOKEN = os.getenv('BOT_TOKEN', 'demo_token')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://work-1-afkscqyawyqtgrne.prod-runtime.all-hands.dev')
PORT = int(os.getenv('PORT', '12000'))

# Bot configuration
BOT_NAME = "ROBIN"
DEVELOPER = "@MLBOR"
MAX_CARDS = 50

# Fake address API
FAKE_ADDRESS_API = "https://randomuser.me/api/"

# User agent for requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"