# UCAM Results Notifier Bot 🎓

An automated bot that monitors your UCAM portal for newly published course results and sends personalized Telegram notifications based on your performance!

## ✨ Features

- 🔐 **Secure Login**: Automatically logs into UCAM portal using encrypted credentials
- 📊 **Smart Monitoring**: Tracks running courses and detects when results are published
- 🎯 **Personalized Messages**: Sends encouraging or brutally honest notifications based on your grade
- 🤖 **Telegram Integration**: Real-time notifications delivered to your Telegram chat
- 🔄 **Robust Retry Logic**: Handles network issues, session expiry, and site slowdowns gracefully
- 📝 **Comprehensive Logging**: Detailed logs for debugging and monitoring
- 🚀 **Lightning Fast**: HTTP-based requests (80-90% faster than browser automation)
- ☁️ **Cloud Ready**: GitHub Actions integration for running 24/7 on cloud servers
- 🔄 **Auto Re-login**: Automatically re-authenticates if session expires
- 💾 **MongoDB Integration**: Persistent state management across runs

## 📋 Bot Versions

### bot_v0.py (Legacy)
Original Selenium-based implementation. Uses a real browser for scraping.

### bot_v1.py (Selenium)
Improved Selenium version with better error handling and retry logic.

### bot_v2.py ⭐ (Recommended)
**New HTTP-based implementation** - Replaces Selenium with direct HTTP requests. 
- **80-90% faster** startup and per-request speed
- **Uses 95% less memory** (10-20MB vs 150-300MB)
- **Eliminates browser dependencies** - no Chrome needed
- **More reliable** - fewer failure points
- **Perfect for cloud deployment** (GitHub Actions)

**Switch to bot_v2.py** - it's production-ready and significantly more efficient!

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Telegram account
- UCAM portal access
- MongoDB Atlas account (free tier works fine)

### Installation

1. **Clone or download the project files**

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # Activate it
   # Windows:
   venv\Scripts\Activate.ps1
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your Telegram Bot**:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Create a new bot: `/newbot`
   - Save your bot token

5. **Get your Telegram Chat ID**:
   - Add your bot to a chat/group
   - Send a message to the chat
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response

6. **Create MongoDB Atlas account** (free tier):
   - Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Create a free cluster
   - Get your connection string (MONGO_URI)

7. **Create `.env` file** in project root:
   ```env
   # UCAM Credentials
   USER_ID=0112345678
   PASSWORD=your_ucam_password
   
   # Telegram
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz
   TELEGRAM_CHAT_ID=your_chat_id
   
   # MongoDB Atlas
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/ucam_bot?retryWrites=true&w=majority
   ```

   ⚠️ **IMPORTANT**: Add `.env` to `.gitignore` - never commit credentials!

## 📖 Usage

### Local Testing

1. **Test the login function**:
   ```bash
   python test.py
   ```
   This verifies your credentials and connection to UCAM.

2. **Run the bot manually**:
   ```bash
   python bot_v2.py
   ```
   The bot will run for up to 5.5 hours, checking every 60 seconds.

### Cloud Deployment (GitHub Actions)

The bot is configured to run automatically on GitHub Actions every 6 hours:

1. Push this repository to GitHub
2. Add secrets in repository settings:
   - `USER_ID`
   - `PASSWORD`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `MONGO_URI`

3. The workflow will automatically trigger every 6 hours

Check the workflow in `.github/workflows/bot.yml` for details.

## 🎭 Message Examples

The bot sends different messages based on your performance:

### 🏆 A Grade (Outstanding):
```
🏆🔥 🗿🗿🗿 ABSOLUTE LEGEND! 🗿🗿🗿

🎊 OUTSTANDING ACHIEVEMENT!
You're absolutely crushing it! 90-100%! 🚀

📚 Course: Artificial Intelligence
🆔 Course ID: CSE 3811
📅 Trimester: 243
💳 Credit: 3.00
🏆 Grade: A
📊 Point: 4.00

🎉 Keep up the amazing work! 🎉
```

### 😔 A- Grade (Almost there):
```
😔💔 😞 Almost there but not quite... 😞

🎊 So close to perfection...
86-89%... You were just a few points away from greatness 😢
```

### 😰 B Grade (Disappointing):
```
😰🙁 😔 This is just average 😔

🎊 Below Expectations
78-81%... Everyone else is probably doing better than this 😢
```

Full grading scale: A, A-, B+, B, B-, C+, C, C-, D+, D, F

## 📁 Project Structure

```
UCAM_Results_Notifier/
├── bot_v0.py                    # Legacy: Original Selenium bot
├── bot_v1.py                    # Legacy: Improved Selenium bot
├── bot_v2.py                    # ⭐ RECOMMENDED: HTTP-based bot (production)
├── test.py                      # Test script for login verification
├── requirements.txt             # Python dependencies
├── .env                         # Your credentials (create this, add to .gitignore)
├── .github/
│   └── workflows/
│       └── bot.yml             # GitHub Actions workflow
├── HOW_IT_WORKS.md             # Detailed explanation of bot_v2
├── logs/                        # Generated log files
└── README.md                    # This file
```

## ⚙️ Configuration

### Environment Variables (.env)

```env
# UCAM Portal Credentials
USER_ID=0112345678              # Your UCAM student ID
PASSWORD=your_password_here     # Your UCAM password

# Telegram Configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz
TELEGRAM_CHAT_ID=6015905885     # Can be negative for groups

# MongoDB Atlas
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/ucam_bot?retryWrites=true&w=majority
```

### Running on Schedule

**GitHub Actions** (Recommended for 24/7 monitoring):
- Runs automatically every 6 hours
- No local machine needed
- Free tier includes 2000 minutes/month
- Configured in `.github/workflows/bot.yml`

**Windows Task Scheduler** (Local):
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., every 2 hours)
4. Action: Run `python bot_v2.py`
5. Set working directory to project folder

**Cron Job** (Linux/macOS):
```bash
# Every 2 hours
0 */2 * * * cd /path/to/project && python bot_v2.py >> logs/bot.log 2>&1
```

## 🔄 How bot_v2.py Works

### Session Management
- Creates a persistent HTTP session with cookies
- Automatically maintains login state across requests
- Handles redirects and CSRF protection

### Login Process
1. GET login page, extract hidden CSRF tokens
2. POST credentials with all required form fields
3. Extract MMI (Menu Mapping Identifier) parameter
4. Store both cookies and MMI for authenticated requests

### Session Validation & Re-login
- Before each request, checks if session is still valid
- If 404 or redirect to login detected, automatically re-logs in
- Ensures bot stays authenticated for the entire 5.5-hour run

### Grade Checking
- Fetches course table every 60 seconds
- Compares with saved state in MongoDB
- Detects new grades by checking for non-empty Grade/Point fields
- Sends notification only once per course

### Data Persistence
- Uses MongoDB Atlas to store state across runs
- Tracks: running courses, notified courses, last update time
- Survives process restarts and network interruptions

For detailed explanation, see [HOW_IT_WORKS.md](HOW_IT_WORKS.md)

## 🔧 Troubleshooting

### Testing

**Test login**:
```bash
python test.py
```
Should output:
```
✅ Logged in successfully! MMI: abc123...
✅ Login test PASSED!
Found X courses...
```

**Check MongoDB connection**:
Verify `MONGO_URI` is correct and cluster is accessible

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| MongoDB connection error | Check `MONGO_URI`, ensure whitelist IP in Atlas |
| No Telegram notifications | Verify bot token and chat ID, ensure bot is in chat |
| Session keeps expiring | Bot now auto re-logins, check logs for errors |
| No grades detected | Run `test.py` to verify login works |

### Debug Mode

Add print statements or increase verbosity:
```python
# In bot_v2.py, add debugging
print(f"DEBUG: Session valid: {is_session_valid()}")
print(f"DEBUG: MMI parameter: {mmi_parameter}")
```

## 📊 Performance Comparison

| Feature | bot_v1 (Selenium) | bot_v2 (HTTP) |
|---------|-------------------|--------------|
| Startup time | 15+ seconds | < 1 second |
| Per-request | 3-5 seconds | 0.5-1 second |
| Memory usage | 150-300MB | 10-20MB |
| CPU usage | High (rendering) | Minimal |
| Chrome required | Yes ✓ | No ✗ |
| Reliability | Medium | High |
| Cloud friendly | Poor | Excellent |

**Result**: bot_v2 is **80-90% faster** and uses **95% less memory**!

## 🔒 Security

- ✅ All credentials in `.env` file (gitignored)
- ✅ No hardcoded passwords in source code
- ✅ HTTPS for all connections (UCAM, Telegram, MongoDB)
- ✅ Session cookies auto-managed by requests library
- ⚠️ Never commit `.env` file to version control
- ⚠️ Keep `MONGO_URI` secret - it contains database credentials

## 🎯 Pro Tips

1. **Start with bot_v2.py** - it's the latest and most efficient
2. **Use MongoDB Atlas free tier** - enough for personal use
3. **Test with `test.py` first** - verify setup before deploying
4. **Monitor logs** - check output if notifications stop coming
5. **Run on GitHub Actions** - get 24/7 monitoring for free
6. **Set longer polling interval** - 120-180 seconds saves resources
7. **Customize messages** - edit `get_message_for_course()` in bot_v2.py

## 📚 Learning

Want to understand how HTTP-based scraping works? Read [HOW_IT_WORKS.md](HOW_IT_WORKS.md) for a detailed explanation of:
- HTTP sessions and cookies
- Form submission and CSRF protection
- HTML parsing with BeautifulSoup
- Session validation and re-authentication
- Comparison with Selenium

## 🤝 Contributing

Found a bug? Have a suggestion? Feel free to:
- Open an issue
- Submit a pull request
- Share feedback

## 📄 License

MIT License - Use freely for personal and educational purposes.

## ❤️ Support

Made with ❤️ for UIU students who want instant result notifications!

Questions? Issues? Check the logs or review [HOW_IT_WORKS.md](HOW_IT_WORKS.md) for technical details.

---

**Last Updated**: February 3, 2026  
**Current Version**: bot_v2.py (HTTP-based, production-ready)
