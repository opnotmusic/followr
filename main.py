import os
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
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)  # Add explicit wait
        
        # Get credentials from environment variables
        self.username = os.environ.get('INSTAGRAM_USERNAME')
        self.password = os.environ.get('INSTAGRAM_PASSWORD')
        self.target_account = os.environ.get('TARGET_ACCOUNT', 'davidguetta')
        self.max_follows = 133
        self.follow_count = 0

    def login(self):
        self.driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(5)
        
        username_field = self.driver.find_element(By.NAME, "username")
        password_field = self.driver.find_element(By.NAME, "password")
        
        username_field.send_keys(self.username)
        password_field.send_keys(self.password)
        time.sleep(2)
        password_field.send_keys(Keys.ENTER)

    def find_followers(self):
        time.sleep(5)
        self.driver.get(f"https://www.instagram.com/{self.target_account}")
        time.sleep(2)
        
        try:
            # Using the CSS selector you found
            followers_link = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "li.xl565be:nth-child(2) > div:nth-child(1) > a:nth-child(1)")
            ))
            followers_link.click()
            
            # Wait for the modal to appear
            modal = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div._aano")
            ))
            
            # Scroll to load enough profiles
            scroll_times = min(10, (self.max_follows // 12) + 2)
            for i in range(scroll_times):
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", modal)
                time.sleep(2)
        
        except TimeoutException:
            print("Could not find followers link or modal. Adding alternative selectors...")
            # Try alternative selectors if the first one fails
            try:
                followers_link = self.wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//a[contains(@href, "/followers")]')
                ))
                followers_link.click()
            except TimeoutException:
                print("Failed to find followers link with alternative selector")
                raise

    def follow(self):
        try:
            # Wait for follow buttons to be present
            all_buttons = self.wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "button._acan")
            ))
            print(f"Found {len(all_buttons)} potential accounts to follow")
            
            for button in all_buttons:
                if self.follow_count >= self.max_follows:
                    print(f"Reached daily follow limit of {self.max_follows}")
                    break
                    
                try:
                    if "Follow" in button.text:
                        button.click()
                        self.follow_count += 1
                        print(f"Followed account {self.follow_count} of {self.max_follows}")
                        time.sleep(1)
                except ElementClickInterceptedException:
                    try:
                        cancel_button = self.wait.until(EC.presence_of_element_located(
                            (By.XPATH, '//button[contains(text(), "Cancel")]')
                        ))
                        cancel_button.click()
                    except:
                        print("Couldn't handle popup, skipping...")
                        continue
                    
        except TimeoutException:
            print("Could not find follow buttons. Instagram page structure might have changed.")
            raise

    def close(self):
        self.driver.quit()
        print(f"Bot finished. Followed {self.follow_count} accounts")

def main():
    bot = InstaFollower()
    try:
        bot.login()
        bot.find_followers()
        bot.follow()
    finally:
        bot.close()

if __name__ == "__main__":
    main()
