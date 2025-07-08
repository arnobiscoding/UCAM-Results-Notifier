from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up Chrome options
options = Options()
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-infobars')
options.add_argument('--disable-extensions')
options.add_argument('--disable-notifications')
options.add_argument('--start-maximized')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
# Remove headless for setup so you can see what's happening
options.add_argument('--headless')

# Set up the driver using webdriver-manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Set up a default WebDriverWait of 10 seconds
wait = WebDriverWait(driver, 10)

RUNNING_COURSES_FILE = 'running_courses.json'

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
            print(f"Login attempt {attempt} failed: {e}")
            if attempt == max_retries:
                return False
            else:
                time.sleep(2)  # Wait before retrying

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

# --- Main Execution ---
USER_ID = os.getenv('USER_ID')
PASSWORD = os.getenv('PASSWORD')

print("Setting up running courses for the current trimester...")

if not login_ucam(driver, USER_ID, PASSWORD, wait):
    print("Login failed!")
    driver.quit()
    exit(1)

try:
    print("Navigating to course registration page...")
    # Navigation with retries
    with_retries(click_xpath, 3, 2, '/html/body/form/div[3]/div[2]/div/div/div/div/div[2]/div[1]/ul/li[5]/a')
    with_retries(click_xpath, 3, 2, '/html/body/form/div[3]/div[2]/div/div/div/div/div[2]/div[1]/ul/li[4]/a')
    with_retries(click_xpath, 3, 2, '/html/body/form/div[3]/div[2]/div/div/div/div/div[2]/div[1]/ul/li[4]/ul/li[1]/a')

    print("Reading course table...")
    # Table reading with retries
    table_html = with_retries(get_table_html, 3, 2)

    # Parse the table
    soup = BeautifulSoup(table_html, 'lxml')
    rows = soup.find_all('tr')
    headers = [th.get_text(strip=True) for th in rows[0].find_all('th')]
    course_data = []
    
    for row in rows[1:]:
        cols = [td.get_text(strip=True) for td in row.find_all('td')]
        if cols:
            course_data.append(dict(zip(headers, cols)))

    # Find running courses (courses with no grade/point yet)
    running_courses = []
    for course in course_data:
        # A course is "running" if it has no grade and no point
        if not course.get('Grade', '').strip() and not course.get('Point', '').strip():
            running_courses.append(course)
    
    print(f"Found {len(running_courses)} running courses:")
    for course in running_courses:
        print(f"  - {course['Course ID'].strip()}: {course['Course Name'].strip()}")
    
    # Save running courses to JSON
    with open(RUNNING_COURSES_FILE, 'w', encoding='utf-8') as f:
        json.dump(running_courses, f, ensure_ascii=False, indent=2)
    
    print(f"Running courses saved to {RUNNING_COURSES_FILE}")
    print("Setup complete! You can now run the bot to monitor for result publications.")

except Exception as e:
    print(f"Error during setup: {e}")
finally:
    driver.quit()
