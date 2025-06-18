import asyncio
import logging
from telethon import TelegramClient, events, Button
from telethon.tl.types import BotInlineResult, InputBotInlineResult
from aiohttp import web
import json
import os
from config import API_ID, API_HASH, BOT_TOKEN, WEBHOOK_URL, PORT, BOT_NAME, DEVELOPER
from card_checker import CardChecker
from database import Database

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class RobinBot:
    def __init__(self):
        self.client = TelegramClient('robin_bot', API_ID, API_HASH)
        self.db = Database()
        self.card_checker = CardChecker()
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        """Setup web routes for the Mini App"""
        # Add CORS middleware
        @web.middleware
        async def cors_middleware(request, handler):
            if request.method == 'OPTIONS':
                response = web.Response(headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                })
                return response
            
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        
        self.app.middlewares.append(cors_middleware)
        
        # API routes first
        self.app.router.add_post('/api/check-cards', self.api_check_cards)
        self.app.router.add_post('/api/add-proxy', self.api_add_proxy)
        self.app.router.add_post('/api/remove-proxy', self.api_remove_proxy)
        self.app.router.add_post('/api/add-shopify-url', self.api_add_shopify_url)
        self.app.router.add_post('/api/remove-shopify-url', self.api_remove_shopify_url)
        self.app.router.add_get('/api/user-data/{user_id}', self.api_get_user_data)
        self.app.router.add_post('/api/update-settings', self.api_update_settings)
        
        # Static files and main page
        self.app.router.add_get('/', self.serve_mini_app)
        self.app.router.add_static('/static', path='static/', name='static')



    async def serve_mini_app(self, request):
        """Serve the Mini App HTML"""
        with open('static/index.html', 'r') as f:
            html_content = f.read()
        return web.Response(text=html_content, content_type='text/html')

    async def api_check_cards(self, request):
        """API endpoint for card checking"""
        try:
            data = await request.json()
            user_id = data.get('user_id')
            cards = data.get('cards', [])
            
            if len(cards) > 50:
                return web.json_response({'error': 'Maximum 50 cards allowed'}, status=400)
            
            # Start card checking process
            result = await self.card_checker.check_cards(user_id, cards)
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Error in card checking API: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def api_add_proxy(self, request):
        """API endpoint to add proxy"""
        try:
            data = await request.json()
            user_id = data.get('user_id')
            proxy = data.get('proxy')
            
            await self.db.add_proxy(user_id, proxy)
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def api_remove_proxy(self, request):
        """API endpoint to remove proxy"""
        try:
            data = await request.json()
            user_id = data.get('user_id')
            proxy = data.get('proxy')
            
            await self.db.remove_proxy(user_id, proxy)
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def api_add_shopify_url(self, request):
        """API endpoint to add Shopify URL"""
        try:
            data = await request.json()
            user_id = data.get('user_id')
            url = data.get('url')
            
            await self.db.add_shopify_url(user_id, url)
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def api_remove_shopify_url(self, request):
        """API endpoint to remove Shopify URL"""
        try:
            data = await request.json()
            user_id = data.get('user_id')
            url = data.get('url')
            
            await self.db.remove_shopify_url(user_id, url)
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def api_get_user_data(self, request):
        """API endpoint to get user data"""
        try:
            logger.info(f"api_get_user_data called with request: {request}")
            user_id = int(request.match_info['user_id'])
            logger.info(f"Getting user data for user_id: {user_id}")
            user_data = await self.db.get_user_data(user_id)
            logger.info(f"User data retrieved: {user_data}")
            
            # If user doesn't exist, create a demo user
            if not user_data.get('user'):
                logger.info(f"User {user_id} doesn't exist, creating demo user")
                await self.db.add_user(user_id, f"demo_user_{user_id}", "Demo User")
                user_data = await self.db.get_user_data(user_id)
                logger.info(f"Demo user created, new data: {user_data}")
            
            return web.json_response(user_data)
            
        except Exception as e:
            logger.error(f"Error in api_get_user_data: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def api_update_settings(self, request):
        """API endpoint to update user settings"""
        try:
            data = await request.json()
            user_id = data.get('user_id')
            settings = data.get('settings')
            
            await self.db.update_user_settings(user_id, settings)
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def start_handler(self, event):
        """Handle /start command"""
        user = await event.get_sender()
        await self.db.add_user(user.id, user.username, user.first_name)
        
        keyboard = [
            [Button.url("🚀 Open ROBIN Mini App", f"{WEBHOOK_URL}?user_id={user.id}")],
            [Button.inline("ℹ️ About", "about")]
        ]
        
        welcome_text = f"""
🤖 **Welcome to {BOT_NAME}!**

Your advanced Shopify card checker bot is ready!

✨ **Features:**
• Card Checker with live status
• Proxy Management
• Shopify URL Management
• Real-time Results

👨‍💻 **Developer:** {DEVELOPER}

Click the button below to open the Mini App!
        """
        
        await event.respond(welcome_text, buttons=keyboard, parse_mode='md')

    async def callback_handler(self, event):
        """Handle callback queries"""
        data = event.data.decode('utf-8')
        
        if data == "about":
            about_text = f"""
ℹ️ **About {BOT_NAME}**

{BOT_NAME} is a professional Shopify card checking bot with advanced features:

🔧 **Features:**
• Multi-threaded card checking
• Proxy rotation support
• Real-time status updates
• Dark-themed modern UI
• Comprehensive error handling

👨‍💻 **Developer:** {DEVELOPER}
🔗 **Version:** 1.0.0

For support, contact {DEVELOPER}
            """
            await event.edit(about_text, parse_mode='md')

    async def setup_handlers(self):
        """Setup event handlers"""
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start(event):
            await self.start_handler(event)

        @self.client.on(events.CallbackQuery())
        async def callback(event):
            await self.callback_handler(event)

    async def start_bot(self):
        """Start the bot"""
        # Start web server first
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        
        logger.info(f"🚀 {BOT_NAME} bot started!")
        logger.info(f"🌐 Mini App available at: {WEBHOOK_URL}")
        logger.info(f"👨‍💻 Developer: {DEVELOPER}")
        
        # Try to connect to Telegram if credentials are provided
        telegram_connected = False
        try:
            if (BOT_TOKEN and BOT_TOKEN not in ['your_bot_token_here', 'demo_token'] and 
                API_HASH and API_HASH not in ['your_api_hash_here', 'demo_hash']):
                await self.client.start(bot_token=BOT_TOKEN)
                await self.setup_handlers()
                telegram_connected = True
                logger.info(f"✅ Telegram bot connected successfully!")
            else:
                logger.info(f"⚠️  Running in demo mode (no Telegram connection)")
        except Exception as e:
            logger.warning(f"⚠️  Telegram connection failed: {e}")
            logger.info(f"🔄 Continuing in web-only mode...")
        
        # Keep the server running
        try:
            if telegram_connected:
                await self.client.run_until_disconnected()
            else:
                # Keep running without Telegram client
                logger.info("🌐 Web server running in demo mode...")
                while True:
                    await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("👋 Bot stopped by user")

if __name__ == '__main__':
    bot = RobinBot()
    asyncio.run(bot.start_bot())