// ROBIN Mini App JavaScript
class RobinApp {
    constructor() {
        this.sessionId = window.ROBIN_SESSION_ID || null;
        this.userId = window.ROBIN_USER_ID || this.getUserId();
        this.isChecking = false;
        this.isPaused = false;
        this.checkingInterval = null;
        this.init();
    }

    getUserId() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('user_id') || '123456789'; // Default for testing
    }

    async validateSession() {
        if (!this.sessionId) {
            this.showAuthError();
            return false;
        }

        try {
            const response = await fetch(`/api/validate-session/${this.sessionId}`);
            if (!response.ok) {
                this.showAuthError();
                return false;
            }
            return true;
        } catch (error) {
            console.error('Session validation error:', error);
            this.showAuthError();
            return false;
        }
    }

    showAuthError() {
        document.body.innerHTML = `
            <div class="auth-error">
                <i class="fas fa-shield-alt" style="font-size: 3rem; color: var(--robin-red); margin-bottom: 1rem;"></i>
                <h2>🔒 Session Expired</h2>
                <p>Your session has expired or is invalid.</p>
                <p>Please restart the bot in Telegram to get a new access link.</p>
                <a href="https://t.me/your_bot_username" class="btn btn-primary">
                    <i class="fab fa-telegram"></i>
                    Open ROBIN Bot
                </a>
            </div>
        `;
    }

    getAuthHeaders() {
        return this.sessionId ? { 'Authorization': `Bearer ${this.sessionId}` } : {};
    }

    async init() {
        // Validate session first
        if (this.sessionId && !(await this.validateSession())) {
            return;
        }

        this.setupEventListeners();
        this.loadUserData();
        this.loadSettings();
        this.updateCardCount();
        this.updateControlButtons();
    }

    setupEventListeners() {
        // Bottom navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const tab = e.currentTarget.dataset.tab;
                this.switchTab(tab);
            });
        });

        // Result tabs
        document.querySelectorAll('.result-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.currentTarget.dataset.tab;
                this.switchResultTab(tabName);
            });
        });

        // Card checker controls
        document.getElementById('start-btn').addEventListener('click', () => this.startChecking());
        document.getElementById('pause-btn').addEventListener('click', () => this.pauseChecking());
        document.getElementById('stop-btn').addEventListener('click', () => this.stopChecking());

        // Card textarea
        document.getElementById('cards-textarea').addEventListener('input', () => this.updateCardCount());

        // Settings
        document.getElementById('add-shopify-url').addEventListener('click', () => this.addShopifyUrl());
        document.getElementById('add-proxy').addEventListener('click', () => this.addProxy());

        // Enter key handlers
        document.getElementById('shopify-url-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.addShopifyUrl();
        });
        document.getElementById('proxy-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.addProxy();
        });
    }

    switchTab(tabName) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }

    switchResultTab(tabName) {
        // Update tabs
        document.querySelectorAll('.result-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update content
        document.querySelectorAll('.result-list').forEach(list => {
            list.classList.remove('active');
        });
        document.getElementById(`${tabName}-results`).classList.add('active');
    }

    updateCardCount() {
        const textarea = document.getElementById('cards-textarea');
        const cards = textarea.value.trim().split('\n').filter(card => card.trim());
        const count = Math.min(cards.length, 50);
        document.getElementById('card-count').textContent = count;
        
        if (count > 50) {
            textarea.style.borderColor = 'var(--danger-color)';
        } else {
            textarea.style.borderColor = 'var(--border-color)';
        }
    }

    async loadUserData() {
        try {
            const url = this.sessionId 
                ? `/api/user-data/${this.userId}?session_id=${this.sessionId}`
                : `/api/user-data/${this.userId}`;
            
            const response = await fetch(url, {
                headers: this.getAuthHeaders()
            });
            const data = await response.json();
            
            if (data.user) {
                document.getElementById('user-name').textContent = data.user.first_name || 'User';
                document.getElementById('user-username').textContent = `@${data.user.username || 'username'}`;
                document.getElementById('user-id').textContent = `ID: ${data.user.id || this.userId}`;
                
                // Try to get user avatar from Telegram
                const avatarUrl = `https://t.me/i/userpic/320/${data.user.username}.jpg`;
                document.getElementById('user-avatar').src = avatarUrl;
                
                // Fallback if avatar fails to load
                document.getElementById('user-avatar').onerror = function() {
                    this.src = 'https://via.placeholder.com/100/6c5ce7/ffffff?text=' + (data.user.first_name?.charAt(0) || 'U');
                };
            }
        } catch (error) {
            console.error('Error loading user data:', error);
        }
    }

    async loadSettings() {
        try {
            const response = await fetch(`/api/user-data/${this.userId}`);
            const data = await response.json();
            
            this.updateShopifyUrlsList(data.shopify_urls || []);
            this.updateProxyList(data.proxies || []);
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    updateShopifyUrlsList(urls) {
        const container = document.getElementById('shopify-urls-list');
        container.innerHTML = '';
        
        if (urls.length === 0) {
            container.innerHTML = '<div style="padding: 1rem; text-align: center; color: var(--text-secondary);">No Shopify URLs added yet</div>';
            return;
        }
        
        urls.forEach(url => {
            const item = document.createElement('div');
            item.className = 'url-item';
            item.innerHTML = `
                <span>${url}</span>
                <button class="remove-btn" onclick="app.removeShopifyUrl('${url}')">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            container.appendChild(item);
        });
    }

    updateProxyList(proxies) {
        const container = document.getElementById('proxy-list');
        container.innerHTML = '';
        
        if (proxies.length === 0) {
            container.innerHTML = '<div style="padding: 1rem; text-align: center; color: var(--text-secondary);">No proxies added yet</div>';
            return;
        }
        
        proxies.forEach(proxy => {
            const item = document.createElement('div');
            item.className = 'proxy-item';
            item.innerHTML = `
                <span>${proxy}</span>
                <button class="remove-btn" onclick="app.removeProxy('${proxy}')">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            container.appendChild(item);
        });
    }

    async addShopifyUrl() {
        const input = document.getElementById('shopify-url-input');
        const url = input.value.trim();
        
        if (!url) {
            this.showNotification('Please enter a Shopify URL', 'error');
            return;
        }
        
        if (!url.includes('shopify') && !url.includes('.com')) {
            this.showNotification('Please enter a valid Shopify URL', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/add-shopify-url', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: this.userId, url })
            });
            
            if (response.ok) {
                input.value = '';
                this.loadSettings();
                this.showNotification('Shopify URL added successfully', 'success');
            } else {
                throw new Error('Failed to add URL');
            }
        } catch (error) {
            this.showNotification('Error adding Shopify URL', 'error');
        }
    }

    async removeShopifyUrl(url) {
        try {
            const response = await fetch('/api/remove-shopify-url', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: this.userId, url })
            });
            
            if (response.ok) {
                this.loadSettings();
                this.showNotification('Shopify URL removed', 'success');
            }
        } catch (error) {
            this.showNotification('Error removing Shopify URL', 'error');
        }
    }

    async addProxy() {
        const input = document.getElementById('proxy-input');
        const proxy = input.value.trim();
        
        if (!proxy) {
            this.showNotification('Please enter a proxy', 'error');
            return;
        }
        
        const proxyPattern = /^[\d.]+:\d+:.+:.+$/;
        if (!proxyPattern.test(proxy)) {
            this.showNotification('Invalid proxy format. Use: ip:port:user:pass', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/add-proxy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: this.userId, proxy })
            });
            
            if (response.ok) {
                input.value = '';
                this.loadSettings();
                this.showNotification('Proxy added successfully', 'success');
            } else {
                throw new Error('Failed to add proxy');
            }
        } catch (error) {
            this.showNotification('Error adding proxy', 'error');
        }
    }

    async removeProxy(proxy) {
        try {
            const response = await fetch('/api/remove-proxy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: this.userId, proxy })
            });
            
            if (response.ok) {
                this.loadSettings();
                this.showNotification('Proxy removed', 'success');
            }
        } catch (error) {
            this.showNotification('Error removing proxy', 'error');
        }
    }

    async startChecking() {
        const textarea = document.getElementById('cards-textarea');
        const cardsText = textarea.value.trim();
        
        if (!cardsText) {
            this.showNotification('Please enter cards to check', 'error');
            return;
        }
        
        const cards = cardsText.split('\n').filter(card => card.trim()).slice(0, 50);
        
        if (cards.length === 0) {
            this.showNotification('No valid cards found', 'error');
            return;
        }
        
        this.isChecking = true;
        this.isPaused = false;
        this.updateControlButtons();
        this.resetResults();
        
        try {
            // Start real Shopify checking process
            const requestBody = { 
                user_id: this.userId, 
                cards,
                session_id: this.sessionId
            };

            const response = await fetch('/api/check-cards', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify(requestBody)
            });
            
            if (response.ok) {
                // Start polling for status updates
                this.startStatusPolling();
                this.showNotification('Card checking started', 'success');
            } else {
                throw new Error('Failed to start checking');
            }
        } catch (error) {
            this.isChecking = false;
            this.updateControlButtons();
            this.showNotification('Error starting card check', 'error');
        }
    }

    pauseChecking() {
        this.isPaused = !this.isPaused;
        const pauseBtn = document.getElementById('pause-btn');
        
        if (this.isPaused) {
            pauseBtn.innerHTML = '<i class="fas fa-play"></i> Resume';
            this.showNotification('Checking paused', 'warning');
        } else {
            pauseBtn.innerHTML = '<i class="fas fa-pause"></i> Pause';
            this.showNotification('Checking resumed', 'success');
        }
    }

    stopChecking() {
        this.isChecking = false;
        this.isPaused = false;
        
        if (this.checkingInterval) {
            clearInterval(this.checkingInterval);
            this.checkingInterval = null;
        }
        
        this.updateControlButtons();
        this.showNotification('Checking stopped', 'warning');
        
        document.getElementById('progress-text').textContent = 'Stopped';
    }

    updateControlButtons() {
        const startBtn = document.getElementById('start-btn');
        const pauseBtn = document.getElementById('pause-btn');
        const stopBtn = document.getElementById('stop-btn');
        
        startBtn.disabled = this.isChecking;
        pauseBtn.disabled = !this.isChecking;
        stopBtn.disabled = !this.isChecking;
        
        if (!this.isChecking) {
            pauseBtn.innerHTML = '<i class="fas fa-pause"></i> Pause';
        }
    }

    resetResults() {
        document.getElementById('total-cards').textContent = '0';
        document.getElementById('live-count').textContent = '0';
        document.getElementById('dead-count').textContent = '0';
        document.getElementById('error-count').textContent = '0';
        document.getElementById('live-tab-count').textContent = '0';
        document.getElementById('dead-tab-count').textContent = '0';
        document.getElementById('error-tab-count').textContent = '0';
        document.getElementById('current-card').textContent = '-';
        document.getElementById('previous-card').textContent = '-';
        document.getElementById('progress-fill').style.width = '0%';
        document.getElementById('progress-text').textContent = 'Starting...';
        
        // Clear result lists
        document.getElementById('live-results').innerHTML = '';
        document.getElementById('dead-results').innerHTML = '';
        document.getElementById('error-results').innerHTML = '';
    }

    startStatusPolling() {
        this.checkingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/user-data/${this.userId}`);
                const data = await response.json();
                
                // Update status (this would need to be implemented in the backend)
                // For now, we'll simulate the checking process
                this.simulateChecking();
                
            } catch (error) {
                console.error('Error polling status:', error);
            }
        }, 1000);
    }

    simulateChecking() {
        // This is a simulation - in real implementation, this would come from the backend
        const textarea = document.getElementById('cards-textarea');
        const cards = textarea.value.trim().split('\n').filter(card => card.trim()).slice(0, 50);
        const totalCards = cards.length;
        
        if (!this.simulationData) {
            this.simulationData = {
                currentIndex: 0,
                results: { LIVE: [], DEAD: [], ERROR: [] }
            };
        }
        
        if (this.simulationData.currentIndex < totalCards && !this.isPaused) {
            const currentCard = cards[this.simulationData.currentIndex];
            const previousCard = this.simulationData.currentIndex > 0 ? cards[this.simulationData.currentIndex - 1] : '-';
            
            // Simulate random result
            const statuses = ['LIVE', 'DEAD', 'ERROR'];
            const weights = [0.05, 0.85, 0.1]; // 5% live, 85% dead, 10% error
            const randomStatus = this.weightedRandom(statuses, weights);
            
            // Generate realistic error messages
            const messages = {
                'LIVE': [
                    'Payment successful - Card is live!',
                    'Transaction approved',
                    'Card charged successfully'
                ],
                'DEAD': [
                    'Card declined by issuer',
                    'Insufficient funds',
                    'Invalid card number',
                    'Card expired',
                    'Invalid CVC/CVV',
                    'Payment validation failed',
                    'Card declined',
                    'Transaction denied'
                ],
                'ERROR': [
                    'Request timeout',
                    'Network error: Connection failed',
                    'Checkout error occurred',
                    'Payment processing error',
                    'HTTP error 503',
                    'Could not find product variant'
                ]
            };
            
            const randomMessage = messages[randomStatus][Math.floor(Math.random() * messages[randomStatus].length)];
            
            // Update current status
            document.getElementById('current-card').textContent = currentCard;
            document.getElementById('previous-card').textContent = previousCard;
            
            // Add result
            const result = {
                card: currentCard,
                status: randomStatus,
                message: randomMessage
            };
            
            this.simulationData.results[randomStatus].push(result);
            this.addResultToList(result);
            
            // Update counters
            const checked = this.simulationData.currentIndex + 1;
            const liveCount = this.simulationData.results.LIVE.length;
            const deadCount = this.simulationData.results.DEAD.length;
            const errorCount = this.simulationData.results.ERROR.length;
            
            document.getElementById('total-cards').textContent = totalCards;
            document.getElementById('live-count').textContent = liveCount;
            document.getElementById('dead-count').textContent = deadCount;
            document.getElementById('error-count').textContent = errorCount;
            document.getElementById('live-tab-count').textContent = liveCount;
            document.getElementById('dead-tab-count').textContent = deadCount;
            document.getElementById('error-tab-count').textContent = errorCount;
            
            // Update progress
            const progress = (checked / totalCards) * 100;
            document.getElementById('progress-fill').style.width = `${progress}%`;
            document.getElementById('progress-text').textContent = `${checked}/${totalCards} cards checked`;
            
            this.simulationData.currentIndex++;
            
            if (this.simulationData.currentIndex >= totalCards) {
                this.stopChecking();
                this.showNotification('Card checking completed', 'success');
                this.simulationData = null;
            }
        }
    }

    weightedRandom(items, weights) {
        const totalWeight = weights.reduce((sum, weight) => sum + weight, 0);
        let random = Math.random() * totalWeight;
        
        for (let i = 0; i < items.length; i++) {
            random -= weights[i];
            if (random <= 0) {
                return items[i];
            }
        }
        
        return items[items.length - 1];
    }

    addResultToList(result) {
        const listId = `${result.status.toLowerCase()}-results`;
        const list = document.getElementById(listId);
        
        const item = document.createElement('div');
        item.className = `result-item ${result.status.toLowerCase()} fade-in`;
        item.innerHTML = `
            <div><strong>${result.card}</strong></div>
            <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">
                ${result.message}
            </div>
        `;
        
        list.insertBefore(item, list.firstChild);
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;
        
        // Set background color based on type
        const colors = {
            success: 'var(--success-color)',
            error: 'var(--danger-color)',
            warning: 'var(--warning-color)',
            info: 'var(--primary-color)'
        };
        
        notification.style.backgroundColor = colors[type] || colors.info;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Add CSS for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new RobinApp();
});

// Add sample data for testing
document.addEventListener('DOMContentLoaded', () => {
    // Add sample cards
    const sampleCards = `4119110093178801|03|2026|065
4119110093952775|02|2028|298
4016360203838000|01|2028|194
4179710127430008|08|2029|176
4119110062040743|07|2027|795`;
    
    document.getElementById('cards-textarea').value = sampleCards;
    
    // Add sample Shopify URLs
    setTimeout(() => {
        const sampleUrls = [
            'https://1pvc.com/products/test-product?srsltid=AfmBOopaj04GssnH8CxFgNy4Wa0ogX0hML7tqRE47pGMKDi0wZ9XTVGu',
            'https://halkab.com.au/products/journey-natural-perfume-oil'
        ];
        
        app.updateShopifyUrlsList(sampleUrls);
        
        // Add sample proxies
        const sampleProxies = [
            '193.233.118.40:61234:user552:r7jugq38',
            '134.202.43.145:61234:user401:i5Jp8KCl',
            '46.232.76.52:61234:user564:ZRyvOBsB'
        ];
        
        app.updateProxyList(sampleProxies);
        app.updateCardCount();
    }, 1000);
});