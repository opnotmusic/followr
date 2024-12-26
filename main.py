import os
import json
import sys
from playwright.sync_api import sync_playwright
import time
from datetime import datetime
import random

class InstagramBot:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.target_account = os.environ.get('TARGET_ACCOUNT', 'davidguetta')
        
        if not self.username or not self.password:
            raise ValueError(
                "Missing credentials! Ensure INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD "
                "are set in your environment variables or GitHub Secrets."
            )
            
        self.max_follows = 133  # Instagram daily limit with safety margin
        self.follow_count = 0
        print(f"Initializing bot for user: {self.username}")
        print(f"Target account to follow: {self.target_account}")

    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            
            try:
                self.login(page)
                self.find_followers(page)
                self.follow_users(page)
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                page.screenshot(path=f"error_{timestamp}.png")
            finally:
                context.close()
                browser.close()

    def login(self, page):
        print("Attempting to log in...")

        # Check for cached session data
        cache_file = "session_cache.json"
        if os.path.exists(cache_file):
            print("Loading session from cache...")
            with open(cache_file, 'r') as f:
                session_data = json.load(f)
                # Restore cookies or session data
                for cookie in session_data.get('cookies', []):
                    page.context.add_cookies([cookie])
                print("Session loaded from cache.")
                return  # Skip login if session is valid
                
        # Navigate to Instagram login page
        page.goto("https://www.instagram.com/accounts/login/")
        page.wait_for_load_state("networkidle")
        
        # Handle cookie dialog if present
        try:
            page.get_by_role("button", name="Allow all cookies").click()
        except:
            print("No cookie dialog found")
        
        # Fill in login form
        print("Entering credentials...")
        page.fill("input[name='username']", self.username)
        page.fill("input[name='password']", self.password)
        page.click("button[type='submit']")
        
        try:
            # Wait for various possible elements/dialogs
            page.wait_for_selector("svg[aria-label='Home'], button:has-text('Save info'), button:has-text('Continue')", timeout=30000)
            
            # Handle unusual login attempt
            unusual_login_button = page.query_selector("button:has-text('Continue')")
            if unusual_login_button:
                unusual_login_button.click()
                print("Handled unusual login attempt")
                page.wait_for_timeout(2000)
                
                print("Waiting for verification code input...")
                page.wait_for_selector("input[name='verificationCode']", timeout=30000)
                verification_code = input("Enter the verification code sent to your email: ")
                
                page.fill("input[name='verificationCode']", verification_code)
                page.click("button[type='submit']")
                print("Submitted verification code")

            # Save session data (cookies) after successful login
            cookies = page.context.cookies()
            with open(cache_file, 'w') as f:
                json.dump({'cookies': cookies}, f)

            print("Session cached successfully.")
            # Handle "Save Login Info" dialog
            save_info_button = page.query_selector("button:has-text('Not Now')")
            if save_info_button:
                save_info_button.click()
                print("Handled 'Save Login Info' dialog")
            
            # Handle notifications dialog
            page.wait_for_timeout(2000)
            notifications_button = page.query_selector("button:has-text('Not Now')")
            if notifications_button:
                notifications_button.click()
                print("Handled notifications dialog")
                
            print("Successfully logged in!")
                
        except Exception as e:
            print(f"Login failed: {str(e)}")
            page.screenshot(path=f"login_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            raise

    def find_followers(self, page):
        print(f"Navigating to {self.target_account}'s profile...")
        page.goto(f"https://www.instagram.com/{self.target_account}/")
        page.wait_for_load_state("networkidle")
        
        print("Looking for followers link...")
        selectors = [
            "a:has-text('followers')",
            f"a[href='/{self.target_account}/followers/']",
            "li:nth-child(2) a"
        ]
        
        for selector in selectors:
            try:
                page.click(selector)
                print(f"Clicked followers link using: {selector}")
                break
            except:
                continue
                
        # Wait for followers modal and scroll
        page.wait_for_selector("div._aano", timeout=10000)
        print("Followers modal loaded")
        
        modal = page.locator("div._aano")
        scroll_count = min(10, (self.max_follows // 12) + 2)
        
        for i in range(scroll_count):
            modal.evaluate("element => element.scrollTop = element.scrollHeight")
            page.wait_for_timeout(random.uniform(500, 1000))
            print(f"Scroll {i + 1}/{scroll_count} completed")

    def follow_users(self, page):
        print("Finding follow buttons...")
        follow_buttons = page.locator("button:has-text('Follow')")
        
        count = min(follow_buttons.count(), self.max_follows)
        print(f"Found {count} potential accounts to follow")
        
        for i in range(count):
            if self.follow_count >= self.max_follows:
                print(f"Reached daily limit of {self.max_follows}")
                break
                
            try:
                button = follow_buttons.nth(i)
                if button.is_visible():
                    page.wait_for_timeout(random.uniform(500, 1500))
                    button.click()
                    self.follow_count += 1
                    print(f"Followed {self.follow_count}/{self.max_follows}")
                    
                    # Handle potential dialogs
                    cancel_button = page.query_selector("button:has-text('Cancel')")
                    if cancel_button:
                        cancel_button.click()
                        print("Handled dialog")
                        
            except Exception as e:
                print(f"Error following user: {str(e)}")
                continue
        
        print(f"Finished following users. Total: {self.follow_count}")

def main():
    try:
        bot = InstaFollower()
        bot.run()
    except Exception as e:
        print(f"Bot failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    username = os.environ.get('INSTAGRAM_USERNAME')
    password = os.environ.get('INSTAGRAM_PASSWORD')
    
    bot = InstagramBot(username, password)
    bot.run()
