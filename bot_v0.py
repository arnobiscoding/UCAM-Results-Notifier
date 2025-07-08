from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
from lxml import etree
import sys
import json
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up Chrome options
options = Options()
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-infobars')  # Disables the 'Chrome is being controlled by automated test software' infobar
options.add_argument('--disable-extensions')  # Disables extensions
options.add_argument('--disable-notifications')  # Disables notifications
options.add_argument('--start-maximized')  # Starts the browser maximized
options.add_argument('--disable-gpu')  # Disables GPU hardware acceleration (useful for some environments)
options.add_argument('--no-sandbox')  # Bypass OS security model (useful for CI environments)
options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
options.add_argument('--headless')  # Uncomment to run in headless mode (no browser UI)

# Set up the driver using webdriver-manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Set up a default WebDriverWait of 10 seconds
wait = WebDriverWait(driver, 10)

RUNNING_COURSES_FILE = 'running_courses.json'
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        response = requests.post(url, data=data)
    except Exception as e:
        pass

def login_ucam(driver, user_id, password, wait, max_retries=3):
    """
    Attempts to log in to UCAM with retries on failure.
    Returns True if login is successful, False otherwise.
    """
    for attempt in range(1, max_retries + 1):
        try:
            driver.get('https://ucam.uiu.ac.bd/Security/Login.aspx')

            # Wait for the username field to be present
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="logMain_UserName"]')))

            # Fill in username
            username_input = driver.find_element(By.XPATH, '//*[@id="logMain_UserName"]')
            username_input.clear()
            username_input.send_keys(user_id)

            # Fill in password
            password_input = driver.find_element(By.XPATH, '//*[@id="logMain_Password"]')
            password_input.clear()
            password_input.send_keys(password)

            # Click login button
            login_button = driver.find_element(By.XPATH, '//*[@id="logMain_Button1"]')
            login_button.click()

            # Wait for the next page to load (e.g., dashboard)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            return True
        except Exception as e:
            if attempt == max_retries:
                return False
            else:
                time.sleep(2)  # Wait before retrying

def get_telegram_updates():
    """Fetch and print the latest messages sent to the bot to help configure the chat ID."""
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates'
    try:
        response = requests.get(url)
    except Exception as e:
        pass

def with_retries(task_fn, max_retries=3, delay=2, *args, **kwargs):
    """Generic retry helper for any task."""
    for attempt in range(1, max_retries + 1):
        try:
            return task_fn(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries:
                raise
            time.sleep(delay)

# --- Main Execution ---
USER_ID = os.getenv('USER_ID')
PASSWORD = os.getenv('PASSWORD')

if not login_ucam(driver, USER_ID, PASSWORD, wait):
    driver.quit()
    sys.exit(1)

def click_xpath(xpath):
    elem = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    elem.click()
    return True

def get_table_html():
    table = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="ctl00_MainContainer_gvRegisteredCourse"]')))
    return table.get_attribute('outerHTML')

try:
    # Navigation with retries
    with_retries(click_xpath, 3, 2, '/html/body/form/div[3]/div[2]/div/div/div/div/div[2]/div[1]/ul/li[5]/a')
    with_retries(click_xpath, 3, 2, '/html/body/form/div[3]/div[2]/div/div/div/div/div[2]/div[1]/ul/li[4]/a')
    with_retries(click_xpath, 3, 2, '/html/body/form/div[3]/div[2]/div/div/div/div/div[2]/div[1]/ul/li[4]/ul/li[1]/a')

    # Table reading with retries
    table_html = with_retries(get_table_html, 3, 2)

    # Parse and print the table in a structured way
    soup = BeautifulSoup(table_html, 'lxml')
    rows = soup.find_all('tr')
    headers = [th.get_text(strip=True) for th in rows[0].find_all('th')]
    course_data = []
    for row in rows[1:]:
        cols = [td.get_text(strip=True) for td in row.find_all('td')]
        if cols:
            course_data.append(dict(zip(headers, cols)))

    # Find running courses
    running_courses = [c for c in course_data if c.get('Course Status', '').lower() == 'running course']
    
    # Load running courses from file (should exist from setup script)
    if not os.path.exists(RUNNING_COURSES_FILE):
        print("No running courses file found. Please run setup_running_courses.py first.")
        driver.quit()
        sys.exit(1)
    
    with open(RUNNING_COURSES_FILE, 'r', encoding='utf-8') as f:
        saved_running_courses = json.load(f)

    # Check if any saved running course now has a grade/point published
    updated_running_courses = saved_running_courses.copy()
    
    for saved_course in saved_running_courses:
        # Find the corresponding course in current data
        current_course = None
        for course in course_data:
            if (course['Course ID'].strip() == saved_course['Course ID'].strip() and
                course['Course Name'].strip() == saved_course['Course Name'].strip() and
                course['Trimester'].strip() == saved_course['Trimester'].strip()):
                current_course = course
                break
        
        if current_course:
            # Check if result is now published (has grade and point)
            current_grade = current_course.get('Grade', '').strip()
            current_point = current_course.get('Point', '').strip()
            
            if current_grade and current_point:
                print(f"Result published for: {current_course['Course Name']} - Grade: {current_grade}, Point: {current_point}")
                
                # Generate encouraging message based on grade
                grade = current_grade.strip()
                point = float(current_point.strip())
                
                # Determine message tone based on grade
                if grade == "A" and point == 4.00:
                    emoji = "🏆🔥"
                    tone = "OUTSTANDING ACHIEVEMENT!"
                    celebration = "🗿🗿🗿 ABSOLUTE LEGEND! 🗿🗿🗿"
                    encouragement = "You're absolutely crushing it! 90-100%! 🚀"
                elif grade == "A-" and point == 3.67:
                    emoji = "😔💔"
                    tone = "So close to perfection..."
                    celebration = "😞 Almost there but not quite... 😞"
                    encouragement = "86-89%... You were just a few points away from greatness �"
                elif grade == "B+" and point == 3.33:
                    emoji = "�📉"
                    tone = "Disappointing Performance"
                    celebration = "💔 Could have been better 💔"
                    encouragement = "82-85%... This is mediocre at best �"
                elif grade == "B" and point == 3.00:
                    emoji = "�🙁"
                    tone = "Below Expectations"
                    celebration = "😔 This is just average 😔"
                    encouragement = "78-81%... Everyone else is probably doing better than this �"
                elif grade == "B-" and point == 2.67:
                    emoji = "��"
                    tone = "Concerning Results"
                    celebration = "😰 This is worrying 😰"
                    encouragement = "74-77%... Your parents probably expected more �"
                elif grade == "C+" and point == 2.33:
                    emoji = "�📉"
                    tone = "Poor Performance"
                    celebration = "😢 This is barely acceptable 😢"
                    encouragement = "70-73%... You're falling behind everyone else 😔"
                elif grade == "C" and point == 2.00:
                    emoji = "��"
                    tone = "Struggling Hard"
                    celebration = "😭 This is embarrassing 😭"
                    encouragement = "66-69%... You really need to step up your game �"
                elif grade == "C-" and point == 1.67:
                    emoji = "🤦‍♂️💩"
                    tone = "This is Bad"
                    celebration = "😤 What happened here? 😤"
                    encouragement = "62-65%... This is really disappointing �"
                elif grade == "D+" and point == 1.33:
                    emoji = "��️"
                    tone = "Terrible Performance"
                    celebration = "� This is unacceptable �"
                    encouragement = "58-61%... You barely scraped by �"
                elif grade == "D" and point == 1.00:
                    emoji = "�☠️"
                    tone = "Rock Bottom"
                    celebration = "😵 Barely surviving 😵"
                    encouragement = "55-57%... This is the minimum to not fail �"
                else:  # F grade
                    emoji = "�⚰️"
                    tone = "Complete Failure"
                    celebration = "😭😭😭 TOTAL DISASTER 😭😭😭"
                    encouragement = "You failed... Time to face the disappointment �"

                message = (
                    f"{emoji} <b>{celebration}</b>\n\n"
                    f"🎊 <b>{tone}</b>\n"
                    f"{encouragement}\n\n"
                    f"📚 Course: <b>{current_course['Course Name'].strip()}</b>\n"
                    f"🆔 Course ID: <b>{current_course['Course ID'].strip()}</b>\n"
                    f"📅 Trimester: {current_course['Trimester'].strip()}\n"
                    f"💳 Credit: {current_course['Credit'].strip()}\n"
                    f"🏆 Grade: <b>{current_grade}</b>\n"
                    f"📊 Point: <b>{current_point}</b>\n\n"
                    f"🎉 Keep up the amazing work! 🎉"
                )
                with_retries(send_telegram_message, 3, 2, message)
                
                # Remove from running_courses after notification
                updated_running_courses = [r for r in updated_running_courses 
                                         if not (r['Course ID'].strip() == current_course['Course ID'].strip() and 
                                               r['Course Name'].strip() == current_course['Course Name'].strip() and
                                               r['Trimester'].strip() == current_course['Trimester'].strip())]
    
    # Update the JSON file
    with open(RUNNING_COURSES_FILE, 'w', encoding='utf-8') as f:
        json.dump(updated_running_courses, f, ensure_ascii=False, indent=2)
    
    print(f"Checked {len(saved_running_courses)} running courses. {len(updated_running_courses)} still pending.")
except Exception as e:
    print(f"Error occurred: {e}")
    send_telegram_message(f"❌ Bot Error: {str(e)}")
finally:
    driver.quit()

