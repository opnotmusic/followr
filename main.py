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
        # Validate credentials first
        self.username = os.environ.get('INSTAGRAM_USERNAME')
        self.password = os.environ.get('INSTAGRAM_PASSWORD')
        self.target_account = os.environ.get('TARGET_ACCOUNT', 'davidguetta')

        # Check if credentials exist
        if not self.username or not self.password:
            raise ValueError(
                "Missing credentials! Ensure INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD "
                "are set in your environment variables or GitHub Secrets."
            )

        print(f"Initializing bot for user: {self.username}")
        print(f"Target account to follow: {self.target_account}")

        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--start-maximized")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.max_follows = 133
        self.follow_count = 0

    def login(self):
        try:
            print("Attempting to log in...")
            self.driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(5)

            # Wait for username field and enter credentials
            username_field = self.wait.until(EC.presence_of_element_located(
                (By.NAME, "username")
            ))
            password_field = self.wait.until(EC.presence_of_element_located(
                (By.NAME, "password")
            ))

            username_field.clear()
            username_field.send_keys(self.username)
            time.sleep(1)
            
            password_field.clear()
            password_field.send_keys(self.password)
            time.sleep(1)
            
            # Click login button instead of sending enter key
            login_button = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[type='submit']")
            ))
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            try:
                self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "svg[aria-label='Home']")
                ))
                print("Successfully logged in!")
            except TimeoutException:
                print("Login might have failed - couldn't find home icon")
                
        except Exception as e:
            print(f"Login failed with error: {str(e)}")
            self.close()
            sys.exit(1)

    def find_followers(self):
        try:
            print(f"Navigating to {self.target_account}'s profile...")
            self.driver.get(f"https://www.instagram.com/{self.target_account}")
            time.sleep(5)

            # Try multiple selectors for the followers link
            selectors = [
                "li.xl565be:nth-child(2) > div:nth-child(1) > a:nth-child(1)",
                "a[href='/" + self.target_account + "/followers/']",
                "a[href*='/followers']",
                "//a[contains(@href, '/followers')]"
            ]

            followers_link = None
            for selector in selectors:
                try:
                    if selector.startswith("//"):
                        followers_link = self.wait.until(EC.element_to_be_clickable(
                            (By.XPATH, selector)
                        ))
                    else:
                        followers_link = self.wait.until(EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, selector)
                        ))
                    break
                except:
                    continue

            if not followers_link:
                raise Exception("Could not find followers link with any selector")

            print("Clicking followers link...")
            followers_link.click()
            time.sleep(3)

            print("Loading followers modal...")
            modal = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div._aano")
            ))

            scroll_times = min(10, (self.max_follows // 12) + 2)
            for i in range(scroll_times):
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", modal)
                time.sleep(2)
                print(f"Scroll {i + 1}/{scroll_times} completed")

        except Exception as e:
            print(f"Error finding followers: {str(e)}")
            raise

    def follow(self):
        try:
            print("Looking for follow buttons...")
            follow_buttons = self.wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "button._acan")
            ))
            print(f"Found {len(follow_buttons)} potential accounts to follow")

            for button in follow_buttons:
                if self.follow_count >= self.max_follows:
                    print(f"Reached daily follow limit of {self.max_follows}")
                    break

                try:
                    button_text = button.text.strip()
                    if button_text == "Follow":
                        button.click()
                        self.follow_count += 1
                        print(f"Followed account {self.follow_count} of {self.max_follows}")
                        time.sleep(1)
                except ElementClickInterceptedException:
                    try:
                        cancel_button = self.wait.until(EC.element_to_be_clickable(
                            (By.XPATH, '//button[contains(text(), "Cancel")]')
                        ))
                        cancel_button.click()
                    except:
                        print("Couldn't handle popup, skipping...")
                        continue

        except Exception as e:
            print(f"Error during follow process: {str(e)}")

    def close(self):
        if hasattr(self, 'driver'):
            self.driver.quit()
        print(f"Bot finished. Followed {self.follow_count} accounts")

def main():
    try:
        bot = InstaFollower()
        bot.login()
        bot.find_followers()
        bot.follow()
    except Exception as e:
        print(f"Bot failed with error: {str(e)}")
        raise
    finally:
        bot.close()

if __name__ == "__main__":
    main()
