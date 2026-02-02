from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import sys
import json
import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# Load environment variables from .env file
load_dotenv()

# Set up Chrome options
options = Options()
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-infobars')
options.add_argument('--disable-extensions')
options.add_argument('--disable-notifications')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-popup-blocking')
options.add_argument('--disable-sync')
options.add_argument('--headless')

# Set up the driver using webdriver-manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Set up a default WebDriverWait of 10 seconds
wait = WebDriverWait(driver, 10)

# MongoDB Configuration
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    print("ERROR: MONGO_URI not found in environment variables. Add it to .env")
    sys.exit(1)

try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.admin.command('ping')  # Test connection
    db = mongo_client['ucam_bot']
    state_collection = db['bot_state']
    print("✅ Connected to MongoDB Atlas successfully.")
except ServerSelectionTimeoutError as e:
    print("❌ ERROR: Failed to connect to MongoDB Atlas. Check MONGO_URI.")
    print(f"   Details: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: MongoDB connection error: {e}")
    sys.exit(1)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
POLL_INTERVAL_SECONDS = 60  # Poll every 30 minutes

# GitHub Actions timeout: 6 hours (21600 seconds). Exit after 5.5 hours to be safe.
MAX_RUNTIME_SECONDS = 5.5 * 3600
start_time = time.time()

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        response = requests.post(url, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")
        return False

def login_ucam(driver, user_id, password, wait, max_retries=3):
    """Attempts to log in to UCAM with retries on failure."""
    for attempt in range(1, max_retries + 1):
        try:
            driver.get('https://ucam.uiu.ac.bd/Security/Login.aspx')
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="logMain_UserName"]')))
            username_input = driver.find_element(By.XPATH, '//*[@id="logMain_UserName"]')
            username_input.clear()
            username_input.send_keys(user_id)
            password_input = driver.find_element(By.XPATH, '//*[@id="logMain_Password"]')
            password_input.clear()
            password_input.send_keys(password)
            login_button = driver.find_element(By.XPATH, '//*[@id="logMain_Button1"]')
            login_button.click()
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            return True
        except Exception as e:
            print(f"Login attempt {attempt} failed: {e}")
            if attempt == max_retries:
                return False
            time.sleep(2)

def with_retries(task_fn, max_retries=3, delay=2, *args, **kwargs):
    """Generic retry helper for any task."""
    for attempt in range(1, max_retries + 1):
        try:
            return task_fn(*args, **kwargs)
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise
            time.sleep(delay)

def click_xpath(xpath):
    elem = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    elem.click()
    return True

def get_table_html():
    table = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="ctl00_MainContainer_gvRegisteredCourse"]')))
    return table.get_attribute('outerHTML')

def extract_courses(table_html):
    """Parse table HTML and return list of course dicts."""
    soup = BeautifulSoup(table_html, 'lxml')
    rows = soup.find_all('tr')
    from bs4 import Tag
    header_row = next((row for row in rows if isinstance(row, Tag) and row.find_all('th')), None)
    if header_row is None:
        raise ValueError("No header row found in table.")
    headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
    course_data = []
    for row in rows[1:]:
        if isinstance(row, Tag):
            cols = [td.get_text(strip=True) for td in row.find_all('td')]
            if cols:
                course_data.append(dict(zip(headers, cols)))
    return course_data

def course_key(course):
    """Return a unique identifier for a course."""
    return (
        course['Course ID'].strip(),
        course['Course Name'].strip(),
        course['Trimester'].strip()
    )

def load_bot_state():
    """Load persistent state from MongoDB. Returns dict with 'running_courses' and 'notified_courses'."""
    try:
        doc = state_collection.find_one({'_id': 'state'})
        if doc:
            return {
                'running_courses': doc.get('running_courses', []),
                'notified_courses': doc.get('notified_courses', [])
            }
    except Exception as e:
        print(f"Failed to load bot state from MongoDB: {e}")
    return {'running_courses': [], 'notified_courses': []}

def save_bot_state(running_courses, notified_courses):
    """Save persistent state to MongoDB."""
    try:
        state_collection.update_one(
            {'_id': 'state'},
            {
                '$set': {
                    'running_courses': running_courses,
                    'notified_courses': notified_courses,
                    'last_updated': (datetime.utcnow() + timedelta(hours=6)).replace(tzinfo=None).isoformat() + '+06:00'
                }
            },
            upsert=True
        )
    except Exception as e:
        print(f"Failed to save bot state to MongoDB: {e}")

def get_message_for_course(course, grade, point):
    """Generate Telegram message based on grade."""
    if grade == "A" and point == 4.00:
        emoji = "🏆🔥"
        tone = "OUTSTANDING ACHIEVEMENT!"
        celebration = "🗿🗿🗿 ABSOLUTE LEGEND! 🗿🗿🗿"
        encouragement = "You're absolutely crushing it! 90-100%! 🚀"
    elif grade == "A-" and point == 3.67:
        emoji = "😔💔"
        tone = "So close to perfection..."
        celebration = "😞 Almost there but not quite... 😞"
        encouragement = "86-89%... You were just a few points away from greatness 😢"
    elif grade == "B+" and point == 3.33:
        emoji = "😰📉"
        tone = "Disappointing Performance"
        celebration = "💔 Could have been better 💔"
        encouragement = "82-85%... This is mediocre at best 😤"
    elif grade == "B" and point == 3.00:
        emoji = "😰🙁"
        tone = "Below Expectations"
        celebration = "😔 This is just average 😔"
        encouragement = "78-81%... Everyone else is probably doing better than this 😢"
    elif grade == "B-" and point == 2.67:
        emoji = "😰😤"
        tone = "Concerning Results"
        celebration = "😰 This is worrying 😰"
        encouragement = "74-77%... Your parents probably expected more 😔"
    elif grade == "C+" and point == 2.33:
        emoji = "😞📉"
        tone = "Poor Performance"
        celebration = "😢 This is barely acceptable 😢"
        encouragement = "70-73%... You're falling behind everyone else 😔"
    elif grade == "C" and point == 2.00:
        emoji = "😭😭"
        tone = "Struggling Hard"
        celebration = "😭 This is embarrassing 😭"
        encouragement = "66-69%... You really need to step up your game 😔"
    elif grade == "C-" and point == 1.67:
        emoji = "🤦‍♂️💩"
        tone = "This is Bad"
        celebration = "😤 What happened here? 😤"
        encouragement = "62-65%... This is really disappointing 😔"
    elif grade == "D+" and point == 1.33:
        emoji = "😰☠️"
        tone = "Terrible Performance"
        celebration = "😤 This is unacceptable 😤"
        encouragement = "58-61%... You barely scraped by 😔"
    elif grade == "D" and point == 1.00:
        emoji = "😵☠️"
        tone = "Rock Bottom"
        celebration = "😵 Barely surviving 😵"
        encouragement = "55-57%... This is the minimum to not fail 😔"
    else:  # F grade
        emoji = "💀⚰️"
        tone = "Complete Failure"
        celebration = "😭😭😭 TOTAL DISASTER 😭😭😭"
        encouragement = "You failed... Time to face the disappointment 😔"

    message = (
        f"{emoji} <b>{celebration}</b>\n\n"
        f"🎊 <b>{tone}</b>\n"
        f"{encouragement}\n\n"
        f"📚 Course: <b>{course['Course Name'].strip()}</b>\n"
        f"🆔 Course ID: <b>{course['Course ID'].strip()}</b>\n"
        f"📅 Trimester: {course['Trimester'].strip()}\n"
        f"💳 Credit: {course['Credit'].strip()}\n"
        f"🏆 Grade: <b>{grade}</b>\n"
        f"📊 Point: <b>{point}</b>\n\n"
        f"🎉 Keep up the amazing work! 🎉"
    )
    return message

# --- Main Execution ---
USER_ID = os.getenv('USER_ID')
PASSWORD = os.getenv('PASSWORD')

if not login_ucam(driver, USER_ID, PASSWORD, wait):
    driver.quit()
    mongo_client.close()
    sys.exit(1)

try:
    # Initial navigation
    print("Navigating to course registration page...")
    with_retries(click_xpath, 3, 2, '/html/body/form/div[3]/div[2]/div/div/div/div/div[2]/div[1]/ul/li[5]/a')
    with_retries(click_xpath, 3, 2, '/html/body/form/div[3]/div[2]/div/div/div/div/div[2]/div[1]/ul/li[4]/a')
    with_retries(click_xpath, 3, 2, '/html/body/form/div[3]/div[2]/div/div/div/div/div[2]/div[1]/ul/li[4]/ul/li[1]/a')

    # Load persistent state from MongoDB
    state = load_bot_state()
    running_courses = state.get('running_courses', [])
    notified_courses = state.get('notified_courses', [])

    # On first run, initialize running_courses from current UCAM data
    if not running_courses:
        print("First run detected. Initializing running courses from UCAM...")
        table_html = with_retries(get_table_html, 3, 2)
        course_data = extract_courses(table_html)
        running_courses = [c for c in course_data if not c.get('Grade', '').strip() and not c.get('Point', '').strip()]
        print(f"Found {len(running_courses)} running courses.")
        save_bot_state(running_courses, notified_courses)

    print(f"✅ Bot started. Monitoring {len(running_courses)} courses. Polling every {POLL_INTERVAL_SECONDS} seconds.")

    # Main polling loop
    while True:
        # Check if we're approaching the 6-hour GitHub Actions timeout
        elapsed_time = time.time() - start_time
        if elapsed_time > MAX_RUNTIME_SECONDS:
            print(f"\n⏰ Approaching 6-hour GitHub Actions timeout. Exiting gracefully after {elapsed_time/3600:.1f} hours.")
            save_bot_state(running_courses, notified_courses)
            break
        
        try:
            print(f"\n[{datetime.now()}] Checking for published grades...")
            # Refresh page to load fresh data
            driver.refresh()
            time.sleep(2)  # Wait for page to load
            table_html = with_retries(get_table_html, 3, 2)
            course_data = extract_courses(table_html)

            for saved_course in running_courses[:]:  # Iterate over copy to allow removal
                key = course_key(saved_course)
                
                # Find current course data
                current_course = None
                for course in course_data:
                    if course_key(course) == key:
                        current_course = course
                        break
                
                if current_course:
                    grade = current_course.get('Grade', '').strip()
                    point = current_course.get('Point', '').strip()
                    
                    # Check if grade was just published
                    if grade and point and key not in notified_courses:
                        print(f"✅ Result published for: {current_course['Course Name']} - Grade: {grade}, Point: {point}")
                        
                        message = get_message_for_course(current_course, grade, float(point))
                        if with_retries(send_telegram_message, 3, 2, message):
                            notified_courses.append(key)
                            running_courses.remove(saved_course)
                            print(f"✅ Notification sent. Removed from tracking.")
                            save_bot_state(running_courses, notified_courses)

            hours_remaining = (MAX_RUNTIME_SECONDS - elapsed_time) / 3600
            print(f"Still tracking {len(running_courses)} courses. Next check in {POLL_INTERVAL_SECONDS//60} minutes. Runtime: {elapsed_time/3600:.1f}h/{MAX_RUNTIME_SECONDS/3600:.1f}h")
            time.sleep(POLL_INTERVAL_SECONDS)

        except Exception as e:
            print(f"Error during poll: {e}")
            time.sleep(60)  # Wait a minute before retrying on error

except Exception as e:
    print(f"Fatal error: {e}")
finally:
    driver.quit()
    mongo_client.close()
