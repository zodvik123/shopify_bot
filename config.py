import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('API_ID', '20587910'))
API_HASH = os.getenv('API_HASH', 'f202401ec4bfa57cbb264908b1187b4b')
BOT_TOKEN = os.getenv('BOT_TOKEN', '7535052644:AAGLGM0IOZNgbY2HEnr76tSt89PTNCkFQfw')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://work-1-afkscqyawyqtgrne.prod-runtime.all-hands.dev')
PORT = int(os.getenv('PORT', '12000'))

# Bot configuration
BOT_NAME = "Raven"
DEVELOPER = "@Backspace_X"
MAX_CARDS = 50

# Fake address API
FAKE_ADDRESS_API = "https://randomuser.me/api/"

# User agent for requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
