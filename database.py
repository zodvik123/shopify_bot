import json
import os
import asyncio
from typing import Dict, List, Any

class Database:
    def __init__(self):
        self.db_file = 'database.json'
        self.data = self.load_data()
        
    def load_data(self) -> Dict:
        """Load data from JSON file"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'users': {},
            'proxies': {},
            'shopify_urls': {},
            'settings': {}
        }
    
    def save_data(self):
        """Save data to JSON file"""
        with open(self.db_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    async def add_user(self, user_id: int, username: str, first_name: str):
        """Add or update user"""
        user_id_str = str(user_id)
        self.data['users'][user_id_str] = {
            'id': user_id,
            'username': username,
            'first_name': first_name,
            'created_at': str(asyncio.get_event_loop().time())
        }
        self.save_data()
    
    async def get_user_data(self, user_id: int) -> Dict:
        """Get user data"""
        user_id_str = str(user_id)
        return {
            'user': self.data['users'].get(user_id_str, {}),
            'proxies': self.data['proxies'].get(user_id_str, []),
            'shopify_urls': self.data['shopify_urls'].get(user_id_str, []),
            'settings': self.data['settings'].get(user_id_str, {})
        }
    
    async def add_proxy(self, user_id: int, proxy: str):
        """Add proxy for user"""
        user_id_str = str(user_id)
        if user_id_str not in self.data['proxies']:
            self.data['proxies'][user_id_str] = []
        
        if proxy not in self.data['proxies'][user_id_str]:
            self.data['proxies'][user_id_str].append(proxy)
            self.save_data()
    
    async def remove_proxy(self, user_id: int, proxy: str):
        """Remove proxy for user"""
        user_id_str = str(user_id)
        if user_id_str in self.data['proxies']:
            if proxy in self.data['proxies'][user_id_str]:
                self.data['proxies'][user_id_str].remove(proxy)
                self.save_data()
    
    async def get_proxies(self, user_id: int) -> List[str]:
        """Get user proxies"""
        user_id_str = str(user_id)
        return self.data['proxies'].get(user_id_str, [])
    
    async def add_shopify_url(self, user_id: int, url: str):
        """Add Shopify URL for user"""
        user_id_str = str(user_id)
        if user_id_str not in self.data['shopify_urls']:
            self.data['shopify_urls'][user_id_str] = []
        
        if url not in self.data['shopify_urls'][user_id_str]:
            self.data['shopify_urls'][user_id_str].append(url)
            self.save_data()
    
    async def remove_shopify_url(self, user_id: int, url: str):
        """Remove Shopify URL for user"""
        user_id_str = str(user_id)
        if user_id_str in self.data['shopify_urls']:
            if url in self.data['shopify_urls'][user_id_str]:
                self.data['shopify_urls'][user_id_str].remove(url)
                self.save_data()
    
    async def get_shopify_urls(self, user_id: int) -> List[str]:
        """Get user Shopify URLs"""
        user_id_str = str(user_id)
        return self.data['shopify_urls'].get(user_id_str, [])
    
    async def update_user_settings(self, user_id: int, settings: Dict):
        """Update user settings"""
        user_id_str = str(user_id)
        self.data['settings'][user_id_str] = settings
        self.save_data()
    
    async def get_user_settings(self, user_id: int) -> Dict:
        """Get user settings"""
        user_id_str = str(user_id)
        return self.data['settings'].get(user_id_str, {})