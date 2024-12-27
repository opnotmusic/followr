import os
import json
import sys
from playwright.sync_api import sync_playwright
import time
from datetime import datetime
import random

class SocialMediaBot:
    def __init__(self):
        self.username = os.environ.get('INSTAGRAM_USERNAME')
        self.password = os.environ.get('INSTAGRAM_PASSWORD')
        self.target = os.environ.get('TARGET_ACCOUNT', 'davidguetta')
        
        if not self.username or not self.password:
            raise ValueError("Missing credentials! Set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD")
        
        self.max_follows = {
            'instagram': 100,
            'threads': 75,
            'twitter': 300,
            'tiktok': 150,
            'soundcloud': 75
        }
        
        self.platform_urls = {
            'instagram': 'https://www.instagram.com/accounts/login/',
            'threads': 'https://www.threads.net/login',
            'twitter': 'https://twitter.com/i/flow/login',
            'tiktok': 'https://www.tiktok.com/login',
            'soundcloud': 'https://soundcloud.com/signin'
        }
        
        self.follow_counts = {platform: 0 for platform in self.max_follows.keys()}

    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            for platform in self.max_follows.keys():
                print(f"\nProcessing {platform}...")
                page = context.new_page()
                
                try:
                    self.login(page, platform)
                    self.find_followers(page, platform)
                    self.follow_users(page, platform)
                except Exception as e:
                    print(f"Error on {platform}: {str(e)}")
                    self.capture_screenshot(page, platform, "error")
                finally:
                    page.close()
            
            context.close()
            browser.close()

    def capture_screenshot(self, page, platform, error_type):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = f"{platform}_{error_type}_{timestamp}.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved: {screenshot_path}")

    def login(self, page, platform):
        cache_file = f"{platform}_session_cache.json"
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                page.context.add_cookies(json.load(f).get('cookies', []))
                return

        page.goto(self.platform_urls[platform])
        page.wait_for_load_state("networkidle")

        if platform in ['instagram', 'threads']:
            self._meta_login(page)
        elif platform == 'twitter':
            self._twitter_login(page)
        elif platform == 'tiktok':
            self._tiktok_login(page)
        else:
            self._soundcloud_login(page)

        cookies = page.context.cookies()
        with open(cache_file, 'w') as f:
            json.dump({'cookies': cookies}, f)

    def _meta_login(self, page):
        try:
            page.get_by_role("button", name="Allow all cookies").click()
        except:
            pass
            
        page.fill("input[name='username']", self.username)
        page.fill("input[name='password']", self.password)
        page.click("button[type='submit']")
        
        self._handle_2fa(page)
        self._handle_dialogs(page)

    def _twitter_login(self, page):
        for attempt in range(5):
            try:
                page.wait_for_selector("input[autocomplete='username']", timeout=60000)
                page.fill("input[autocomplete='username']", self.username)
                page.click("span:has-text('Next')")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1}: Waiting for Twitter username input failed: {str(e)}")
                time.sleep(2)  # Wait before retrying

    for attempt in range(5):
        try:
            page.wait_for_selector("input[name='password']", timeout=60000)
            page.fill("input[name='password']", self.password)
            page.click("div[data-testid='LoginForm_Login_Button']")
            break
        except Exception as e:
            print(f"Attempt {attempt + 1}: Waiting for Twitter password input failed: {str(e)}")
            time.sleep(2)  # Wait before retrying

    def _tiktok_login(self, page):
        for attempt in range(5):
            try:
                page.wait_for_selector("button:has-text('Use phone / email / username')", timeout=60000)
                page.click("button:has-text('Use phone / email / username')")
                page.click("a:has-text('Log in with email or username')")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1}: Waiting for TikTok login button failed: {str(e)}")
                self.capture_screenshot(page, "tiktok", "login_button_error")
                time.sleep(2)

        for attempt in range(5):
            try:
                page.wait_for_selector("input[name='username']", timeout=60000)
                page.fill("input[name='username']", self.username)
                page.fill("input[type='password']", self.password)
                page.click("button[type='submit']")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1}: Waiting for TikTok username input failed: {str(e)}")
                self.capture_screenshot(page, "tiktok", "username_input_error")
                time.sleep(2)

    def _soundcloud_login(self, page):
        for attempt in range(5):
            try:
                page.wait_for_selector("button:has-text('Accept cookies')", timeout=60000)
                page.click("button:has-text('Accept cookies')")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1}: Waiting for SoundCloud accept cookies button failed: {str(e)}")
                self.capture_screenshot(page, "soundcloud", "accept_cookies_error")
                time.sleep(2)

        for attempt in range(5):
            try:
                page.wait_for_selector("button:has-text('Continue with email')", timeout=60000)
                page.click("button:has-text('Continue with email')")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1}: Waiting for SoundCloud continue with email button failed: {str(e)}")
                self.capture_screenshot(page, "soundcloud", "continue_email_error")
                time.sleep(2)

        for attempt in range(5):
            try:
                page.wait_for_selector("input[name='email']", timeout=60000)
                page.fill("input[name='email']", self.username)
                page.fill("input[name='password']", self.password)
                page.click("button[type='submit']")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1}: Waiting for SoundCloud email input failed: {str(e)}")
                self.capture_screenshot(page, "soundcloud", "email_input_error")
                time.sleep(2)

    def _handle_2fa(self, page):
        if page.query_selector("input[name='verificationCode']"):
            code = input("Enter 2FA code: ")
            page.fill("input[name='verificationCode']", code)
            page.click("button[type='submit']")

    def _handle_dialogs(self, page):
        for selector in ["button:has-text('Not Now')", "button:has-text('Skip')", 
                        "button:has-text('Cancel')", "button:has-text('Close')"]:
            try:
                if button := page.query_selector(selector):
                    button.click()
                    page.wait_for_timeout(1000)
            except:
                continue

    def find_followers(self, page, platform):
        print(f"Finding followers for {self.target} on {platform}")
        
        urls = {
            'instagram': f"https://www.instagram.com/{self.target}/",
            'threads': f"https://www.threads.net/{self.target}/",
            'twitter': f"https://twitter.com/{self.target}/followers",
            'tiktok': f"https://www.tiktok.com/@{self.target}/followers",
            'soundcloud': f"https://soundcloud.com/{self.target}/followers"
        }
        
        page.goto(urls[platform])
        page.wait_for_load_state("networkidle")
        
        selectors = {
            'instagram': [f"a:has-text('followers')", f"a[href='/{self.target}/followers/']"],
            'threads': [f"a:has-text('followers')", f"a[href='/{self.target}/followers/']"],
            'twitter': ["[data-testid='followers']"],
            'tiktok': ["span:has-text('Followers')"],
            'soundcloud': ["a:has-text('Followers')", ".infoStats__followersCount"]
        }
        
        for selector in selectors.get(platform, []):
            try:
                page.click(selector)
                break
            except Exception as e:
                print(f"Error finding followers on {platform}: {str(e)}")
                self.capture_screenshot(page, platform, "find_followers_error")
                continue              
                
        page.wait_for_timeout(2000)
        self._scroll_followers(page, platform)

    def _scroll_followers(self, page, platform):
        scroll_count = min(10, (self.max_follows[platform] // 12) + 2)
        for i in range(scroll_count):
            page.keyboard.press('PageDown')
            page.wait_for_timeout(random.uniform(500, 1000))

    def follow_users(self, page, platform):
        selectors = {
            'instagram': "button:has-text('Follow')",
            'threads': "button:has-text('Follow')",
            'twitter': "[data-testid='follow']",
            'tiktok': "button:has-text('Follow')",
            'soundcloud': "button.sc-button-follow"
        }
        
        limit_messages = {
            'instagram': ["Try Again Later", "Action Blocked", "Limit Reached"],
            'threads': ["Try Again Later", "Action Blocked", "Limit Reached"],
            'twitter': ["Rate limit exceeded", "You are unable to follow more"],
            'tiktok': ["Follow limit reached", "Too many follows"],
            'soundcloud': ["Follow limit reached", "Daily limit exceeded"]
        }
        
        buttons = page.locator(selectors[platform])
        count = min(buttons.count(), self.max_follows[platform])
        
        for i in range(count):
            if self.follow_counts[platform] >= self.max_follows[platform]:
                break
                
            try:
                if button := buttons.nth(i):
                    if button.is_visible():
                        page.wait_for_timeout(random.uniform(500, 1500))
                        button.click()
                        
                        # Check for limit messages
                        for message in limit_messages[platform]:
                            if page.get_by_text(message, exact=False).is_visible():
                                print(f"Follow limit detected on {platform}. Moving to next platform.")
                                return
                        
                        self.follow_counts[platform] += 1
                        print(f"Followed {self.follow_counts[platform]}/{self.max_follows[platform]}")
                        self._handle_dialogs(page)
            except Exception as e:
                print(f"Error following user: {str(e)}")

if __name__ == "__main__":
    try:
        bot = SocialMediaBot()
        bot.run()
    except Exception as e:
        print(f"Bot failed: {str(e)}")
        sys.exit(1)
