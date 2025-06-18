# 🤖 ROBIN - Shopify Card Checker Bot

A professional Telegram bot with Mini App for checking Shopify cards with advanced features and dark-themed UI.

## 🌟 Features

### 🎯 Card Checker
- **Multi-card support**: Check up to 50 cards simultaneously
- **Real-time status**: Live updates with progress tracking
- **Smart categorization**: Results sorted into LIVE, DEAD, and ERROR
- **Pause/Resume**: Full control over checking process
- **Progress tracking**: Visual progress bar and detailed statistics

### 🔧 Advanced Settings
- **Proxy Management**: Add/remove proxies with rotation support
- **Shopify URL Management**: Multiple store support
- **Fake Address Generation**: Automatic billing/shipping details
- **Error Handling**: Comprehensive error management

### 🎨 Modern UI
- **Dark Theme**: Sleek ROBIN-inspired design
- **Responsive**: Works on all devices
- **Intuitive Navigation**: Bottom tab navigation
- **Real-time Updates**: Live status and results

### 👤 User Management
- **Profile Display**: Shows Telegram user info and avatar
- **Settings Persistence**: User preferences saved
- **Multi-user Support**: Each user has isolated data

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Telegram API credentials
- Bot token from @BotFather

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd shopify_bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure credentials**:
   - Copy `.env.example` to `.env`
   - Get API credentials from https://my.telegram.org/apps
   - Get bot token from @BotFather
   - Update `.env` with your credentials

4. **Start the bot**:
   ```bash
   python start.py
   ```

### Configuration

Edit `.env` file:
```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
WEBHOOK_URL=https://your-domain.com
PORT=12000
```

## 📱 Usage

### Starting the Bot
1. Send `/start` to your bot on Telegram
2. Click "🚀 Open ROBIN Mini App"
3. The Mini App will open with full functionality

### Card Checking
1. Go to **Checker** tab
2. Enter cards in format: `number|month|year|cvv`
3. Click **Start** to begin checking
4. Monitor progress and results in real-time

### Managing Settings
1. Go to **Settings** tab
2. Add Shopify product URLs
3. Configure proxies for rotation
4. Settings are saved automatically

## 🔧 API Endpoints

The bot provides several API endpoints for the Mini App:

- `GET /` - Serve Mini App
- `POST /api/check-cards` - Start card checking
- `POST /api/add-proxy` - Add proxy
- `POST /api/remove-proxy` - Remove proxy
- `POST /api/add-shopify-url` - Add Shopify URL
- `POST /api/remove-shopify-url` - Remove Shopify URL
- `GET /api/user-data/{user_id}` - Get user data

## 📊 Sample Data

### Test Cards
```
4119110093178801|03|2026|065
4119110093952775|02|2028|298
4016360203838000|01|2028|194
4179710127430008|08|2029|176
4119110062040743|07|2027|795
```

### Test Shopify URLs
```
https://1pvc.com/products/test-product
https://halkab.com.au/products/journey-natural-perfume-oil
```

### Test Proxies
```
193.233.118.40:61234:user552:r7jugq38
134.202.43.145:61234:user401:i5Jp8KCl
46.232.76.52:61234:user564:ZRyvOBsB
```

## 🏗️ Architecture

### Backend Components
- **bot.py**: Main bot logic and web server
- **card_checker.py**: Card checking engine
- **database.py**: Data persistence layer
- **config.py**: Configuration management

### Frontend Components
- **index.html**: Mini App structure
- **style.css**: ROBIN dark theme styling
- **script.js**: Interactive functionality

### Key Features
- **Async Processing**: Non-blocking card checking
- **Proxy Rotation**: Automatic proxy switching
- **Error Recovery**: Graceful error handling
- **Real-time Updates**: Live status monitoring

## 🔒 Security Features

- **Input Validation**: All inputs are validated
- **Rate Limiting**: Prevents abuse
- **Error Handling**: Secure error messages
- **Data Isolation**: User data separation

## 🎨 UI/UX Features

- **Dark Theme**: Professional ROBIN styling
- **Responsive Design**: Mobile-first approach
- **Smooth Animations**: Enhanced user experience
- **Intuitive Controls**: Easy-to-use interface

## 🛠️ Development

### Project Structure
```
shopify_bot/
├── bot.py              # Main bot application
├── card_checker.py     # Card checking logic
├── database.py         # Data management
├── config.py          # Configuration
├── start.py           # Startup script
├── requirements.txt   # Dependencies
├── static/           # Mini App files
│   ├── index.html    # App structure
│   ├── style.css     # Styling
│   └── script.js     # Functionality
└── README.md         # Documentation
```

### Adding Features
1. Backend: Extend classes in respective modules
2. Frontend: Update HTML/CSS/JS in static/
3. API: Add endpoints in bot.py
4. Database: Extend database.py for persistence

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Developer

**@MLBOR** - Professional Telegram Bot Developer

## 🤝 Support

For support and questions:
- Contact: @MLBOR
- Issues: Create an issue in the repository
- Documentation: Check this README

## 🔄 Updates

- **v1.0.0**: Initial release with full functionality
- Dark theme implementation
- Multi-card checking support
- Proxy rotation system
- Real-time status updates

---

**⚡ ROBIN - Advanced Shopify Card Checker Bot**
*Professional, Fast, Reliable*