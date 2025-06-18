import asyncio
import logging
import uuid
import json
from datetime import datetime, timedelta
from telethon import TelegramClient, events, Button
from telethon.tl.types import BotInlineResult, InputBotInlineResult
from aiohttp import web
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
        self.active_sessions = {}  # Store UUID sessions with expiry
        self.setup_routes()
        
    def setup_routes(self):
        """Setup web routes for the Mini App"""
        # Add CORS middleware
        @web.middleware
        async def cors_middleware(request, handler):
            if request.method == 'OPTIONS':
                response = web.Response(headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, DELETE',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                })
                return response
            
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, DELETE'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        self.app.middlewares.append(cors_middleware)
        
        # Authentication routes
        self.app.router.add_get('/auth/{session_id}', self.serve_authenticated_app)
        self.app.router.add_get('/api/validate-session/{session_id}', self.validate_session)
        
        # API routes with authentication
        self.app.router.add_post('/api/check-cards', self.api_check_cards)
        self.app.router.add_post('/api/add-proxy', self.api_add_proxy)
        self.app.router.add_post('/api/remove-proxy', self.api_remove_proxy)
        self.app.router.add_post('/api/add-shopify-url', self.api_add_shopify_url)
        self.app.router.add_post('/api/remove-shopify-url', self.api_remove_shopify_url)
        self.app.router.add_get('/api/user-data/{user_id}', self.api_get_user_data)
        self.app.router.add_post('/api/update-settings', self.api_update_settings)
        
        # Fallback route for unauthorized access
        self.app.router.add_get('/', self.serve_unauthorized)
        self.app.router.add_static('/static', path='static/', name='static')

    def generate_session(self, user_id):
        """Generate a new session UUID for user"""
        session_id = str(uuid.uuid4())
        expiry = datetime.now() + timedelta(hours=24)  # 24 hour session
        
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.now(),
            'expires_at': expiry
        }
        
        # Clean up expired sessions
        self.cleanup_expired_sessions()
        
        return session_id
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired_sessions = [
            session_id for session_id, data in self.active_sessions.items()
            if data['expires_at'] < now
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
    
    def validate_session_id(self, session_id):
        """Validate if session ID is active and not expired"""
        if session_id not in self.active_sessions:
            return None
        
        session_data = self.active_sessions[session_id]
        if session_data['expires_at'] < datetime.now():
            del self.active_sessions[session_id]
            return None
        
        return session_data['user_id']

    async def serve_unauthorized(self, request):
        """Serve unauthorized access page"""
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ROBIN - Unauthorized Access</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
            <link rel="stylesheet" href="/static/style.css">
        </head>
        <body>
            <div class="auth-error">
                <i class="fas fa-shield-alt" style="font-size: 3rem; color: var(--robin-red); margin-bottom: 1rem;"></i>
                <h2>🔒 Access Denied</h2>
                <p>This Mini App can only be accessed through the official ROBIN Telegram bot.</p>
                <p>Please start the bot in Telegram and use the provided link to access the application.</p>
                <a href="https://t.me/your_bot_username" class="btn btn-primary">
                    <i class="fab fa-telegram"></i>
                    Open ROBIN Bot
                </a>
            </div>
        </body>
        </html>
        """
        return web.Response(text=html_content, content_type='text/html')

    async def serve_authenticated_app(self, request):
        """Serve the Mini App for authenticated users"""
        session_id = request.match_info['session_id']
        user_id = self.validate_session_id(session_id)
        
        if not user_id:
            return await self.serve_unauthorized(request)
        
        # Load and modify the HTML to include session validation
        with open('static/index.html', 'r') as f:
            html_content = f.read()
        
        # Inject session validation script
        session_script = f"""
        <script>
            window.ROBIN_SESSION_ID = '{session_id}';
            window.ROBIN_USER_ID = {user_id};
            
            // Validate session on load
            fetch('/api/validate-session/{session_id}')
                .then(response => {{
                    if (!response.ok) {{
                        window.location.href = '/';
                    }}
                }})
                .catch(() => {{
                    window.location.href = '/';
                }});
        </script>
        """
        
        # Insert before closing head tag
        html_content = html_content.replace('</head>', f'{session_script}</head>')
        
        return web.Response(text=html_content, content_type='text/html')

    async def validate_session(self, request):
        """API endpoint to validate session"""
        session_id = request.match_info['session_id']
        user_id = self.validate_session_id(session_id)
        
        if user_id:
            return web.json_response({'valid': True, 'user_id': user_id})
        else:
            return web.json_response({'valid': False}, status=401)

    async def api_check_cards(self, request):
        """API endpoint for card checking with session validation"""
        try:
            # Validate session from headers or body
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                session_id = auth_header[7:]
                user_id = self.validate_session_id(session_id)
                if not user_id:
                    return web.json_response({'error': 'Invalid session'}, status=401)
            else:
                data = await request.json()
                session_id = data.get('session_id')
                user_id = self.validate_session_id(session_id) if session_id else None
                if not user_id:
                    return web.json_response({'error': 'Invalid session'}, status=401)
            
            data = await request.json()
            cards = data.get('cards', [])
            
            if len(cards) > 50:
                return web.json_response({'error': 'Maximum 50 cards allowed'}, status=400)
            
            # Start real card checking process
            result = await self.card_checker.check_cards_real(user_id, cards)
            return web.json_response(result)
            
        except Exception as e:
            logger.error(f"Error in card checking API: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def api_add_proxy(self, request):
        """API endpoint to add proxy with session validation"""
        try:
            data = await request.json()
            session_id = data.get('session_id')
            user_id = self.validate_session_id(session_id)
            
            if not user_id:
                return web.json_response({'error': 'Invalid session'}, status=401)
            
            proxy = data.get('proxy')
            await self.db.add_proxy(user_id, proxy)
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def api_remove_proxy(self, request):
        """API endpoint to remove proxy with session validation"""
        try:
            data = await request.json()
            session_id = data.get('session_id')
            user_id = self.validate_session_id(session_id)
            
            if not user_id:
                return web.json_response({'error': 'Invalid session'}, status=401)
            
            proxy = data.get('proxy')
            await self.db.remove_proxy(user_id, proxy)
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def api_add_shopify_url(self, request):
        """API endpoint to add Shopify URL with session validation"""
        try:
            data = await request.json()
            session_id = data.get('session_id')
            user_id = self.validate_session_id(session_id)
            
            if not user_id:
                return web.json_response({'error': 'Invalid session'}, status=401)
            
            url = data.get('url')
            await self.db.add_shopify_url(user_id, url)
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def api_remove_shopify_url(self, request):
        """API endpoint to remove Shopify URL with session validation"""
        try:
            data = await request.json()
            session_id = data.get('session_id')
            user_id = self.validate_session_id(session_id)
            
            if not user_id:
                return web.json_response({'error': 'Invalid session'}, status=401)
            
            url = data.get('url')
            await self.db.remove_shopify_url(user_id, url)
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def api_get_user_data(self, request):
        """API endpoint to get user data with session validation"""
        try:
            user_id = int(request.match_info['user_id'])
            session_id = request.query.get('session_id')
            
            validated_user_id = self.validate_session_id(session_id)
            if not validated_user_id or validated_user_id != user_id:
                return web.json_response({'error': 'Invalid session'}, status=401)
            
            logger.info(f"api_get_user_data called with request: {request}")
            logger.info(f"Getting user data for user_id: {user_id}")
            
            user_data = await self.db.get_user_data(user_id)
            logger.info(f"User data retrieved: {user_data}")
            
            return web.json_response(user_data)
            
        except Exception as e:
            logger.error(f"Error getting user data: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def api_update_settings(self, request):
        """API endpoint to update settings with session validation"""
        try:
            data = await request.json()
            session_id = data.get('session_id')
            user_id = self.validate_session_id(session_id)
            
            if not user_id:
                return web.json_response({'error': 'Invalid session'}, status=401)
            
            settings = data.get('settings', {})
            await self.db.update_user_settings(user_id, settings)
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)

    async def start_bot(self):
        """Start the Telegram bot"""
        await self.client.start(bot_token=BOT_TOKEN)
        logger.info(f"🤖 {BOT_NAME} bot started successfully!")
        
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            user = await event.get_sender()
            user_id = user.id
            
            # Generate session for user
            session_id = self.generate_session(user_id)
            
            # Create authenticated Mini App URL
            mini_app_url = f"{WEBHOOK_URL}/auth/{session_id}"
            
            # Store user in database
            await self.db.add_user(user_id, user.username or 'Unknown', user.first_name or 'User')
            
            welcome_message = f"""
🤖 **Welcome to {BOT_NAME}!**

🔥 **Advanced Shopify Card Checker**
✅ Real-time card validation
✅ Multiple Shopify store support  
✅ Proxy rotation
✅ Detailed error reporting

🚀 **Click the button below to access your secure Mini App:**

⚡ *Session expires in 24 hours*
🔒 *Secure UUID authentication*

Developer: {DEVELOPER}
            """
            
            keyboard = [
                [Button.url("🚀 Open ROBIN Mini App", mini_app_url)]
            ]
            
            await event.respond(welcome_message, buttons=keyboard)

        @self.client.on(events.NewMessage(pattern='/app'))
        async def app_handler(event):
            user = await event.get_sender()
            user_id = user.id
            
            # Generate new session
            session_id = self.generate_session(user_id)
            mini_app_url = f"{WEBHOOK_URL}/auth/{session_id}"
            
            keyboard = [
                [Button.url("🚀 Open ROBIN Mini App", mini_app_url)]
            ]
            
            await event.respond("🔗 **Access your Mini App:**", buttons=keyboard)

        @self.client.on(events.NewMessage(pattern='/help'))
        async def help_handler(event):
            help_text = f"""
🤖 **{BOT_NAME} Help**

**Commands:**
/start - Start the bot and get Mini App access
/app - Get new Mini App link
/help - Show this help message
/status - Check bot status

**Features:**
🔥 Real Shopify card checking
🛡️ Secure UUID authentication
🌐 Multiple proxy support
📊 Live progress tracking
🎯 Detailed error messages

**Card Format:**
`4111111111111111|12|2025|123`

**Proxy Format:**
`ip:port:username:password`

Developer: {DEVELOPER}
            """
            await event.respond(help_text)

        @self.client.on(events.NewMessage(pattern='/status'))
        async def status_handler(event):
            user = await event.get_sender()
            user_id = user.id
            
            # Count active sessions for user
            user_sessions = sum(1 for session_data in self.active_sessions.values() 
                              if session_data['user_id'] == user_id)
            
            status_text = f"""
📊 **{BOT_NAME} Status**

🟢 **Bot Status:** Online
👤 **Your User ID:** `{user_id}`
🔑 **Active Sessions:** {user_sessions}
⏰ **Server Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🔥 **Ready for card checking!**
            """
            await event.respond(status_text)

    async def start_web_server(self):
        """Start the web server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        
        logger.info(f"🌐 Web server started on port {PORT}")
        logger.info(f"🔗 Mini App URL: {WEBHOOK_URL}")

    async def run(self):
        """Run both bot and web server"""
        await asyncio.gather(
            self.start_bot(),
            self.start_web_server()
        )
        
        logger.info(f"🚀 {BOT_NAME} is fully operational!")
        
        # Keep running
        await self.client.run_until_disconnected()

if __name__ == '__main__':
    bot = RobinBot()
    asyncio.run(bot.run())