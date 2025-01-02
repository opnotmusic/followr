import os
import json
import sys
import logging
from playwright.sync_api import sync_playwright
import time
from datetime import datetime
import random

# Configure logging
logging.basicConfig(level=logging.INFO)

class SocialMediaBot:
    def __init__(self):
        self.username = os.environ.get('INSTAGRAM_USERNAME')
        self.password = os.environ.get('INSTAGRAM_PASSWORD')
        self.target = os.environ.get('TARGET_ACCOUNT', 'davidguetta')

        if not self.username or not self.password:
            raise ValueError("Missing credentials! Set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD")

        self.max_follows = {
            'instagram': 30,
            'threads': 35,
            'twitter': 30,
            'tiktok': 30,
            'soundcloud': 35
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
                logging.info("Processing %s...", platform)
                page = context.new_page()

                try:
                    self.login(page, platform)
                    self.find_followers(page, platform)
                    self.follow_users(page, platform)
                except Exception as e:
                    logging.error("Error on %s: %s", platform, str(e))
                    self.capture_screenshot(page, platform, "error")
                finally:
                    page.close()

            context.close()
            browser.close()

    def capture_screenshot(self, page, platform, error_type):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = f"{platform}_{error_type}_{timestamp}.png"
        page.screenshot(path=screenshot_path)
        logging.info("Screenshot saved: %s", screenshot_path)

    def login(self, page, platform):
        cache_file = f"{platform}_session_cache.json"

        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                page.context.add_cookies(json.load(f).get('cookies', []))
            return

        page.goto(self.platform_urls[platform])
        page.wait_for_load_state("networkidle")

        try:
            if platform in ['instagram', 'threads']:
                self._meta_login(page)
            elif platform == 'twitter':
                self._twitter_login(page)
            elif platform == 'tiktok':
                self._tiktok_login(page)
            else:
                self._soundcloud_login(page)
        except Exception as e:
            logging.error("Login failed on %s: %s", platform, str(e))
            self.capture_screenshot(page, platform, "login_error")

        cookies = page.context.cookies()
        with open(cache_file, 'w') as f:
            json.dump({'cookies': cookies}, f)

    def find_followers(self, page, platform):
        logging.info("Finding followers for %s on %s", self.target, platform)

        urls = {
            'instagram': f"https://www.instagram.com/{self.target}/",
            'threads': f"https://www.threads.net/{self.target}/",
            'twitter': f"https://twitter.com/{self.target}/",
            'tiktok': f"https://www.tiktok.com/@{self.target}/",
            'soundcloud': f"https://soundcloud.com/{self.target}/"
        }

        page.goto(urls[platform])
        page.wait_for_load_state("networkidle")

        selectors = {
            'instagram': [".x1i10hfl", "._a6hd"],
            'threads': [".x1i10hfl", "._a6hd"],
            'twitter': [".css-146c3p1"],
            'tiktok': [".css-1hig5p0-SpanUnit"],
            'soundcloud': [".infoStats__statLink"]
        }

        for selector in selectors.get(platform, []):
            try:
                page.click(selector)
                break
            except Exception as e:
                logging.error("Error finding followers on %s: %s", platform, str(e))
                self.capture_screenshot(page, platform, "find_followers_error")
                continue

        page.wait_for_timeout(3000)
        self._scroll_followers(page, platform)

    def _scroll_followers(self, page, platform):
        scroll_count = min(10, (self.max_follows[platform] // 12) + 2)
        for _ in range(scroll_count):
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

                        for message in limit_messages[platform]:
                            if page.get_by_text(message, exact=False).is_visible():
                                logging.info("Follow limit detected on %s. Moving to next platform.", platform)
                                return

                        self.follow_counts[platform] += 1
                        logging.info("Followed %d/%d on %s", self.follow_counts[platform], self.max_follows[platform], platform)
                        self._handle_dialogs(page)
            except Exception as e:
                logging.error("Error following user on %s: %s", platform, str(e))

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
            except Exception as e:
                logging.error("Failed to handle dialog: %s", str(e))

if __name__ == "__main__":
    try:
        bot = SocialMediaBot()
        bot.run()
    except Exception as e:
        logging.error("Bot failed: %s", str(e))
        sys.exit(1)
