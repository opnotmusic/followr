import os
import sys
from playwright.sync_api import sync_playwright
import time
from datetime import datetime
import random

class InstaFollower:
    def __init__(self):
        self.username = os.environ.get('INSTAGRAM_USERNAME')
        self.password = os.environ.get('INSTAGRAM_PASSWORD')
        self.target_account = os.environ.get('TARGET_ACCOUNT', 'davidguetta')
        
        if not self.username or not self.password:
            raise ValueError(
                "Missing credentials! Ensure INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD "
                "are set in your environment variables or GitHub Secrets."
            )
            
        self.max_follows = 133
        self.follow_count = 0
        print(f"Initializing bot for user: {self.username}")
        print(f"Target account to follow: {self.target_account}")

    def run(self):
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Create new page
            page = context.new_page()
            
            try:
                self.login(page)
                self.find_followers(page)
                self.follow_users(page)
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                # Save screenshot for debugging
                page.screenshot(path=f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            finally:
                browser.close()

    def login(self, page):
        print("Attempting to log in...")
        
        # Navigate to Instagram login page
        page.goto("https://www.instagram.com/accounts/login/")
        page.wait_for_load_state("networkidle")
        
        # Fill in login form
        print("Entering credentials...")
        page.fill("input[name='username']", self.username)
        page.fill("input[name='password']", self.password)
        
        # Click the login button
        page.click("button[type='submit']")
        
        # Wait for navigation and handle dialogs
        try:
            # Extend timeout to handle slow page loads
            page.wait_for_selector("svg[aria-label='Home'], button:has-text('Save info'), button:has-text('Continue')", timeout=30000)
            
            # Handle unusual login attempt
            unusual_login_button = page.query_selector("button:has-text('Continue')")
            if unusual_login_button:
                unusual_login_button.click()
                print("Handled unusual login attempt by clicking 'Continue'")
                page.wait_for_timeout(2000)  # Allow time for the next page to load
                
                # Wait for the code input field
                print("Waiting for verification code input field...")
                page.wait_for_selector("input[name='verificationCode']", timeout=30000)
                
                # Pause and ask the user for the code
                verification_code = input("Enter the verification code sent to your email: ")
                
                # Fill in the verification code
                page.fill("input[name='verificationCode']", verification_code)
                page.click("button[type='submit']")
                print("Entered verification code and submitted.")
                
            # Handle the "Save Login Info" dialog if it appears
            save_info_button = page.query_selector("button:has-text('Not Now')")
            if save_info_button:
                save_info_button.click()
                print("Handled 'Save Login Info' dialog")
            
            # Handle the notifications dialog if it appears
            page.wait_for_timeout(2000)
            notifications_button = page.query_selector("button:has-text('Not Now')")
            if notifications_button:
                notifications_button.click()
                print("Handled notifications dialog")
                
            print("Successfully logged in!")
                
        except Exception as e:
            print(f"Login failed: {str(e)}")
            # Capture a screenshot for debugging
            page.screenshot(path=f"login_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            raise

    def find_followers(self, page):
        print(f"Navigating to {self.target_account}'s profile...")
        page.goto(f"https://www.instagram.com/{self.target_account}/")
        page.wait_for_load_state("networkidle")
        
        # Click followers link - try multiple selectors
        print("Looking for followers link...")
        selectors = [
            "a:has-text('followers')",
            f"a[href='/{self.target_account}/followers/']",
            "li:nth-child(2) a"  # Common position for followers link
        ]
        
        for selector in selectors:
            try:
                page.click(selector)
                print(f"Found and clicked followers link using selector: {selector}")
                break
            except:
                continue
                
        # Wait for followers modal
        page.wait_for_selector("div._aano", timeout=10000)
        print("Followers modal loaded")
        
        # Scroll to load followers
        print("Loading followers...")
        modal = page.locator("div._aano")
        for i in range(min(10, (self.max_follows // 12) + 2)):
            modal.evaluate("element => element.scrollTop = element.scrollHeight")
            page.wait_for_timeout(random.uniform(500, 1000))  # Random delay between scrolls
            print(f"Scroll {i + 1} completed")

    def follow_users(self, page):
        print("Looking for follow buttons...")
        follow_buttons = page.locator("button:has-text('Follow')")
        
        count = follow_buttons.count()
        count = min(count, self.max_follows)
        print(f"Found {count} potential accounts to follow")
        
        for i in range(count):
            if self.follow_count >= self.max_follows:
                print(f"Reached daily follow limit of {self.max_follows}")
                break
                
            try:
                button = follow_buttons.nth(i)
                if button.is_visible():
                    # Random delay before clicking
                    page.wait_for_timeout(random.uniform(500, 1500))
                    button.click()
                    self.follow_count += 1
                    print(f"Followed account {self.follow_count} of {self.max_follows}")
                    
                    # Handle any dialogs that might appear
                    cancel_button = page.query_selector("button:has-text('Cancel')")
                    if cancel_button:
                        cancel_button.click()
                        print("Handled dialog")
                        
            except Exception as e:
                print(f"Error following user: {str(e)}")
                continue
        
        print(f"Finished following users. Total followed: {self.follow_count}")

def main():
    try:
        bot = InstaFollower()
        bot.run()
    except Exception as e:
        print(f"Bot failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
