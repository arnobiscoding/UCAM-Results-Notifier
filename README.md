# UCAM Results Notifier Bot 🎓

An automated bot that monitors your UCAM portal for newly published course results and sends personalized Telegram notifications based on your performance!

## ✨ Features

- 🔐 **Secure Login**: Automatically logs into UCAM portal using encrypted credentials
- 📊 **Smart Monitoring**: Tracks running courses and detects when results are published
- 🎯 **Personalized Messages**: Sends encouraging or brutally honest notifications based on your grade
- 🤖 **Telegram Integration**: Real-time notifications delivered to your Telegram chat
- 🔄 **Robust Retry Logic**: Handles network issues and site slowdowns gracefully
- 📝 **Comprehensive Logging**: Detailed logs for debugging and monitoring
- ⏰ **Task Scheduler Ready**: Designed to run automatically via Windows Task Scheduler

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Google Chrome browser
- Telegram account
- UCAM portal access

### Installation

1. **Clone or download the project files**

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
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

6. **Create `.env` file** with your credentials:
   ```env
   USER_ID=your_ucam_student_id
   PASSWORD=your_ucam_password
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

## 📋 Usage

### Initial Setup (Run once per trimester)

1. **Run the setup script**:
   ```bash
   # Option 1: Use batch file (Windows)
   setup_running_courses.bat
   
   # Option 2: Run directly
   python setup_running_courses.py
   ```

This creates `running_courses.json` with all your current courses that don't have results yet.

### Regular Monitoring

1. **Manual run**:
   ```bash
   # Option 1: Use batch file (Windows)
   run_bot.bat
   
   # Option 2: Run directly
   python bot_v0.py
   ```

2. **Automated monitoring** (recommended):
   - Use Windows Task Scheduler
   - Point to `run_bot.bat`
   - Set to run every 1-2 hours during result publication periods

## 🎭 Message Examples

The bot sends different messages based on your performance:

### 🏆 A Grade (Outstanding):
```
🏆🔥 🗿🗿🗿 ABSOLUTE LEGEND! 🗿🗿🗿

🎊 OUTSTANDING ACHIEVEMENT!
You're absolutely crushing it! 90-100%! 🚀

📚 Course: Data Structures and Algorithms
🆔 Course ID: CSE 2141
📅 Trimester: 243
💳 Credit: 3.00
🏆 Grade: A
📊 Point: 4.00

🎉 Keep up the amazing work! 🎉
```

### 😔 A- Grade (So close...):
```
😔💔 😞 Almost there but not quite... 😞

🎊 So close to perfection...
86-89%... You were just a few points away from greatness 😢

📚 Course: Physics II
🆔 Course ID: PHY 1112
📅 Trimester: 243
💳 Credit: 3.00
🏆 Grade: A-
📊 Point: 3.67

🎉 Keep up the amazing work! 🎉
```

### 😰 B Grade (Disappointing):
```
😰🙁 😔 This is just average 😔

🎊 Below Expectations
78-81%... Everyone else is probably doing better than this 😢

📚 Course: Calculus I
🆔 Course ID: MAT 1101
📅 Trimester: 243
💳 Credit: 3.00
🏆 Grade: B
📊 Point: 3.00

🎉 Keep up the amazing work! 🎉
```

## 📁 Project Structure

```
UCAM_Results_Notifier/
├── bot_v0.py                    # Main monitoring bot
├── setup_running_courses.py     # Setup script (run once per trimester)
├── run_bot.bat                  # Windows batch file for running bot
├── setup_running_courses.bat    # Windows batch file for setup
├── requirements.txt             # Python dependencies
├── running_courses.json         # Generated file tracking your courses
├── .env                         # Your credentials (create this)
├── logs/                        # Generated log files
│   ├── bot_scheduler.log        # Bot execution logs
│   ├── bot_output.log          # Bot output and errors
│   └── setup.log               # Setup script logs
└── README.md                   # This file
```

## ⚙️ Configuration

### Environment Variables (.env)
```env
# UCAM Portal Credentials
USER_ID=0112345678              # Your UCAM student ID
PASSWORD=your_password_here     # Your UCAM password

# Telegram Configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWXyz  # Bot token from BotFather
TELEGRAM_CHAT_ID=6015905885     # Your chat/group ID (can be negative)
```

### Windows Task Scheduler Setup

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily, every 2 hours)
4. Action: Start a program
5. Program: `C:\path\to\your\project\run_bot.bat`
6. Start in: `C:\path\to\your\project\`

## 🔧 Troubleshooting

### Common Issues

**❌ ModuleNotFoundError: No module named 'selenium'**
```bash
# Ensure virtual environment is activated and install dependencies
pip install -r requirements.txt
```

**❌ Chrome driver issues**
- The script auto-downloads Chrome driver
- Ensure Google Chrome is installed and updated

**❌ Login failures**
- Check your UCAM credentials in `.env`
- Verify UCAM portal is accessible

**❌ No Telegram notifications**
- Verify bot token and chat ID
- Ensure bot is added to the chat/group
- Test with a simple message first

**❌ "No running courses file found"**
- Run `setup_running_courses.py` first
- This should be done once per trimester

### Debug Mode

For troubleshooting, you can disable headless mode in the scripts:
```python
# Comment out this line to see the browser
# options.add_argument('--headless')
```

## 📊 Logs

The bot generates detailed logs in the `logs/` directory:

- **`bot_scheduler.log`**: Execution timestamps and status
- **`bot_output.log`**: Detailed bot output and any errors
- **`setup.log`**: Setup script execution logs

## 🔒 Security

- ✅ Credentials stored in `.env` file (add to `.gitignore`)
- ✅ No hardcoded passwords in source code
- ✅ Secure HTTPS connections to UCAM and Telegram
- ⚠️ Keep your `.env` file private and secure

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests!

## 📄 License

MIT License - feel free to use and modify as needed.

## 🎯 Pro Tips

1. **Run setup script** at the beginning of each trimester
2. **Schedule the bot** to run every 1-2 hours during exam periods
3. **Check logs** if notifications stop coming
4. **Test thoroughly** before relying on automated scheduling
5. **Keep Chrome updated** for best compatibility

---

Made with ❤️ for UIU students who want instant result notifications! 