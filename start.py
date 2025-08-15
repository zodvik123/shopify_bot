#!/usr/bin/env python3
"""
ROBIN Bot Startup Script
A simple script to start the bot with sample configuration
"""

import os
import asyncio
from bot import RobinBot

# Create sample .env file if it doesn't exist
if not os.path.exists('.env'):
    sample_env = """# ROBIN Bot Configuration
# Get these values from https://my.telegram.org/apps
API_ID=20587910
API_HASH=f202401ec4bfa57cbb264908b1187b4b
BOT_TOKEN=7535052644:AAGLGM0IOZNgbY2HEnr76tSt89PTNCkFQfw

# Webhook configuration
WEBHOOK_URL=https://work-1-afkscqyawyqtgrne.prod-runtime.all-hands.dev
PORT=12000
"""
    
    with open('.env', 'w') as f:
        f.write(sample_env)
    
    print("📝 Created .env file with sample configuration")
    print("🔧 Please edit .env file with your actual Telegram API credentials")
    print("📖 Get API credentials from: https://my.telegram.org/apps")
    print("🤖 Get bot token from: @BotFather on Telegram")
    print("")

def main():
    print("🚀 Starting ROBIN Bot...")
    print("👨‍💻 Developer: @Backspace_X")
    print("🌐 Mini App will be available at: https://work-1-afkscqyawyqtgrne.prod-runtime.all-hands.dev")
    print("")
    
    # Check if .env has been configured
    if not os.getenv('BOT_TOKEN') or os.getenv('BOT_TOKEN') == 'your_bot_token_here':
        print("⚠️  Warning: Bot token not configured!")
        print("📝 Please edit .env file with your actual credentials")
        print("🔄 Starting in demo mode...")
        print("")
    
    try:
        bot = RobinBot()
        asyncio.run(bot.start_bot())
    except KeyboardInterrupt:
        print("\n👋 ROBIN Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        print("🔧 Please check your configuration in .env file")

if __name__ == '__main__':
    main()
