import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import ElementClickInterceptedException
import time

class InstaFollower:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Get credentials from environment variables
        self.username = os.environ.get('INSTAGRAM_USERNAME')
        self.password = os.environ.get('INSTAGRAM_PASSWORD')
        self.target_account = os.environ.get('TARGET_ACCOUNT', 'davidguetta')
        self.max_follows = 133  # Daily follow limit
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
        
        followers = self.driver.find_element(By.XPATH, 
            '//a[contains(@href, "/followers")]')
        followers.click()
        time.sleep(2)
        
        modal = self.driver.find_element(By.CSS_SELECTOR, "div._aano")
        
        # Only scroll enough to get slightly more than max_follows buttons
        # Assuming each scroll loads about 12 users
        scroll_times = min(10, (self.max_follows // 12) + 2)
        
        for i in range(scroll_times):
            self.driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight", modal)
            time.sleep(2)

    def follow(self):
        all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button._acan")
        print(f"Found {len(all_buttons)} potential accounts to follow")
        
        for button in all_buttons:
            if self.follow_count >= self.max_follows:
                print(f"Reached daily follow limit of {self.max_follows}")
                break
                
            try:
                if "Follow" in button.text:  # Only click if it's a Follow button
                    button.click()
                    self.follow_count += 1
                    print(f"Followed account {self.follow_count} of {self.max_follows}")
                    time.sleep(1)
            except ElementClickInterceptedException:
                try:
                    cancel_button = self.driver.find_element(By.XPATH, 
                        '//button[contains(text(), "Cancel")]')
                    cancel_button.click()
                except:
                    print("Couldn't handle popup, skipping...")
                    continue
                
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
