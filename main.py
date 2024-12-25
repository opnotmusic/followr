import os
import sys
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
import time

class InstaFollower:
    def __init__(self):
        # Validate credentials
        self.username = os.environ.get('INSTAGRAM_USERNAME')
        self.password = os.environ.get('INSTAGRAM_PASSWORD')
        self.target_account = os.environ.get('TARGET_ACCOUNT', 'davidguetta')

        if not self.username or not self.password:
            raise ValueError(
                "Missing credentials! Ensure INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD "
                "are set in your environment variables or GitHub Secrets."
            )

        print(f"Initializing bot for user: {self.username}")
        print(f"Target account to follow: {self.target_account}")

        # Enhanced Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--lang=en-US')
        
        # Add modern user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional Chrome preferences
        chrome_prefs = {
            'profile.default_content_setting_values.notifications': 2,
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'profile.default_content_settings.popups': 0,
            'download.default_directory': '/tmp'
        }
        chrome_options.add_experimental_option('prefs', chrome_prefs)
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Execute CDP commands to prevent detection
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.wait = WebDriverWait(self.driver, 20)  # Increased wait time
        self.max_follows = 133
        self.follow_count = 0

    def login(self):
        try:
            print("Attempting to log in...")
            self.driver.get("https://www.instagram.com/")
            time.sleep(5)  # Wait for initial page load
            
            # Go to login page
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(5)

            # Check if we're on the login page
            print("Looking for login fields...")
            
            # Try different selectors for username and password fields
            try:
                username_field = self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[name='username']")
                ))
                password_field = self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[name='password']")
                ))
            except TimeoutException:
                print("Couldn't find standard login fields, trying alternative selectors...")
                username_field = self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[aria-label='Phone number, username, or email']")
                ))
                password_field = self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input[aria-label='Password']")
                ))

            print("Found login fields, entering credentials...")
            
            # Clear fields first
            username_field.clear()
            password_field.clear()
            
            # Type credentials with random delays
            for char in self.username:
                username_field.send_keys(char)
                time.sleep(0.1)
            
            for char in self.password:
                password_field.send_keys(char)
                time.sleep(0.1)

            # Find and click login button
            login_button = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[type='submit']")
            ))
            print("Clicking login button...")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(10)
            
            # Verify login success
            try:
                self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "svg[aria-label='Home']")
                ))
                print("Successfully logged in!")
            except TimeoutException:
                print("Login verification failed - checking for additional dialogs...")
                
                # Check for and handle various post-login dialogs
                try:
                    save_info_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Not Now')]")
                    save_info_button.click()
                    print("Handled 'Save Info' dialog")
                except:
                    pass
                
                try:
                    notifications_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Not Now')]")
                    notifications_button.click()
                    print("Handled notifications dialog")
                except:
                    pass

        except Exception as e:
            print(f"Login failed with error: {str(e)}")
            print("Current page source:")
            print(self.driver.page_source[:1000])  # Print first 1000 chars of page source for debugging
            self.close()
            sys.exit(1)

    # ... [rest of the methods remain the same] ...

def main():
    bot = None
    try:
        bot = InstaFollower()
        bot.login()
        bot.find_followers()
        bot.follow()
    except Exception as e:
        print(f"Bot failed with error: {str(e)}")
    finally:
        if bot:
            bot.close()

if __name__ == "__main__":
    main()
