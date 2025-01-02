import os
import json
import sys
import logging
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import time
from datetime import datetime
import random
from cryptography.fernet import Fernet
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Encryption key for session cookies (generate and store securely)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
fernet = Fernet(ENCRYPTION_KEY.encode())

class SocialMediaBot:
    def __init__(self):
        self.username = os.getenv('INSTAGRAM_USERNAME')
        self.password = os.getenv('INSTAGRAM_PASSWORD')
        self.target = os.getenv('TARGET_ACCOUNT', 'davidguetta')

        if not self.username or not self.password:
            raise ValueError("Missing credentials! Set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in the .env file.")

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
            'twitter': 'https://x.com/i/flow/login',
            'tiktok': 'https://www.tiktok.com/login',
            'soundcloud': 'https://soundcloud.com/signin'
        }

        self.selectors = {
            'login': {
                'instagram': "input[name='username']",
                'threads': "input[name='username']",
                'twitter': "input[name='email']",
                'tiktok': "input[name='username']",
                'soundcloud': "input[name='email']"
            },
            'password': {
                'instagram': "input[name='password']",
                'threads': "input[name='password']",
                'twitter': "input[name='password']",
                'tiktok': "input[type='password']",
                'soundcloud': "input[name='password']"
            },
            'submit': {
                'instagram': "button[type='submit']",
                'threads': "button[type='submit']",
                'twitter': "button:has-text('Log in')",
                'tiktok': "button[type='submit']",
                'soundcloud': "button[type='submit']"
            }
        }

        self.follow_counts = {platform: 0 for platform in self.max_follows.keys()}

    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            def process_platform(platform):
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 800},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()
                try:
                    logging.info("Processing %s...", platform)
                    self.login(page, platform)
                    self.find_followers(page, platform)
                    self.follow_users(page, platform)
                except Exception as e:
                    logging.error("Error on %s: %s", platform, str(e))
                    self.capture_screenshot(page, platform, "error")
                finally:
                    page.close()
                    context.close()

            with ThreadPoolExecutor() as executor:
                executor.map(process_platform, self.max_follows.keys())

            browser.close()

    def encrypt_cookies(self, cookies):
        return fernet.encrypt(json.dumps(cookies).encode()).decode()

    def decrypt_cookies(self, encrypted):
        return json.loads(fernet.decrypt(encrypted.encode()).decode())

    def capture_screenshot(self, page, platform, error_type):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = f"{platform}_{error_type}_{timestamp}.png"
        page.screenshot(path=screenshot_path)
        logging.info("Screenshot saved: %s", screenshot_path)

    def login(self, page, platform):
        cache_file = f"{platform}_session_cache.json"

        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    encrypted = f.read()
                    cookies = self.decrypt_cookies(encrypted)
                    page.context.add_cookies(cookies.get('cookies', []))
                logging.info("Loaded session cookies for %s", platform)
                return
            except Exception as e:
                logging.warning("Failed to load session cookies for %s: %s", platform, str(e))

        page.goto(self.platform_urls[platform], timeout=15000)
        page.wait_for_load_state("networkidle")

        retry_attempts = 3
        for attempt in range(retry_attempts):
            try:
                self._perform_login(page, platform)
                cookies = page.context.cookies()
                with open(cache_file, 'w') as f:
                    encrypted = self.encrypt_cookies({'cookies': cookies})
                    f.write(encrypted)
                logging.info("Session cookies saved for %s", platform)
                break
            except Exception as e:
                logging.error("Login attempt %d failed on %s: %s", attempt + 1, platform, str(e))
                if attempt == retry_attempts - 1:
                    raise

    def _perform_login(self, page, platform):
        page.fill(self.selectors['login'][platform], self.username, timeout=5000)
        page.fill(self.selectors['password'][platform], self.password, timeout=5000)
        page.click(self.selectors['submit'][platform], timeout=5000)

        self._handle_2fa(page)
        self._handle_dialogs(page)

    def find_followers(self, page, platform):
        logging.info("Finding followers for %s on %s", self.target, platform)

        target_urls = {
            'instagram': f"https://www.instagram.com/{self.target}/",
            'threads': f"https://www.threads.net/{self.target}/",
            'twitter': f"https://x.com/{self.target}/followers",
            'tiktok': f"https://www.tiktok.com/@{self.target}/",
            'soundcloud': f"https://soundcloud.com/{self.target}/followers"
        }

        page.goto(target_urls[platform], timeout=15000)
        page.wait_for_load_state("networkidle")
        self._scroll_followers(page, platform)

    def _scroll_followers(self, page, platform):
        scroll_count = min(10, (self.max_follows[platform] // 12) + 2)
        for _ in range(scroll_count):
            page.evaluate("window.scrollBy(0, window.innerHeight)")
            page.wait_for_timeout(random.uniform(500, 1000))

    def follow_users(self, page, platform):
        selectors = {
            'instagram': "button:has-text('Follow')",
            'threads': "button:has-text('Follow')",
            'twitter': "[data-testid='follow']",
            'tiktok': "button:has-text('Follow')",
            'soundcloud': "button.sc-button-follow"
        }

        buttons = page.locator(selectors[platform])

        try:
            for i in range(min(buttons.count(), self.max_follows[platform])):
                if self.follow_counts[platform] >= self.max_follows[platform]:
                    break

                button = buttons.nth(i)
                if button.is_visible():
                    self._close_overlays(page)
                    button.click(timeout=5000)
                    page.wait_for_timeout(random.uniform(500, 1500))

                    self.follow_counts[platform] += 1
                    logging.info("Followed %d/%d on %s", self.follow_counts[platform], self.max_follows[platform], platform)
        except Exception as e:
            logging.error("Error following users on %s: %s", platform, str(e))

    def _handle_2fa(self, page):
        if page.locator("input[name='verificationCode']").is_visible():
            code = input("Enter 2FA code: ")
            page.fill("input[name='verificationCode']", code, timeout=5000)
            page.click("button[type='submit']", timeout=5000)

    def _handle_dialogs(self, page):
        for selector in ["button:has-text('Not Now')", "button:has-text('Skip')", 
                         "button:has-text('Cancel')", "button:has-text('Close')"]:
            try:
                dialog = page.locator(selector)
                if dialog.is_visible():
                    dialog.click(timeout=5000)
                    page.wait_for_timeout(1000)
            except Exception as e:
                logging.error("Failed to handle dialog: %s", str(e))

    def _close_overlays(self, page):
        overlay_selectors = ["div[role='dialog']", "div.modal", "div.overlay"]
        for selector in overlay_selectors:
            try:
                overlay = page.locator(selector)
                if overlay.is_visible():
                    logging.info("Closing overlay: %s", selector)
                    overlay.locator("button:has-text('Close')").click(timeout=3000)
                    page.wait_for_timeout(1000)
            except Exception:
                pass

if __name__ == "__main__":
    try:
        bot = SocialMediaBot()
        bot.run()
    except Exception as e:
        logging.error("Bot failed: %s", str(e))
        sys.exit(1)
