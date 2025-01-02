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
        self.google_email = os.getenv('GOOGLE_EMAIL')
        self.google_password = os.getenv('GOOGLE_PASSWORD')
        self.target = os.getenv('TARGET_ACCOUNT', 'davidguetta')

        if not self.google_email or not self.google_password:
            raise ValueError("Missing Google credentials! Set GOOGLE_EMAIL and GOOGLE_PASSWORD in secrets.")

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

        self.follow_counts = {platform: 0 for platform in self.max_follows.keys()}

    def run(self):
        def process_platform(platform):
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
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
                    browser.close()

        with ThreadPoolExecutor() as executor:
            executor.map(process_platform, self.max_follows.keys())

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
        cache_file = f"{platform}_google_session_cache.json"

        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cookies = self.decrypt_cookies(f.read())
                    page.context.add_cookies(cookies.get('cookies', []))
                logging.info(f"Loaded Google session cookies for {platform}.")
                return
            except Exception as e:
                logging.warning(f"Failed to load Google session cookies for {platform}: {e}")

        # Perform login using Google
        self._perform_google_login(page, platform)

        # Cache cookies after successful login
        cookies = page.context.cookies()
        with open(cache_file, 'w') as f:
            f.write(self.encrypt_cookies({'cookies': cookies}))
        logging.info(f"Google session cookies saved for {platform}.")

    def _perform_google_login(self, page, platform):
        try:
            logging.info(f"Logging into {platform} using Google/Instagram...")
            button_texts = {
                'tiktok': "Continue with Google",
                'threads': "Continue with Instagram",
                'soundcloud': "Continue with Google",
                'twitter': "Log in with Google",
                'instagram': "Log in with Google",
            }

            button_text = button_texts.get(platform, "Log in with Google")
            page.click(f"button:has-text('{button_text}')", timeout=15000)
            page.wait_for_load_state("networkidle")

            # Handle Google's or Instagram's login page
            if platform in ['tiktok', 'soundcloud', 'twitter', 'instagram']:
                page.fill("input[type='email']", self.google_email, timeout=15000)
                page.click("button:has-text('Next')", timeout=15000)
                page.wait_for_timeout(2000)  # Adjust as needed
                page.fill("input[type='password']", self.google_password, timeout=15000)
                page.click("button:has-text('Next')", timeout=15000)
                self._wait_for_phone_confirmation(page)

            logging.info(f"Successfully logged into {platform} via Google/Instagram.")
        except Exception as e:
            logging.error(f"Google/Instagram login failed for {platform}: {e}")
            raise RuntimeError(f"Login error on {platform}: {e}")

    def _wait_for_phone_confirmation(self, page):
        try:
            logging.info("Waiting for phone confirmation...")
            page.wait_for_load_state("networkidle", timeout=300000)  # Wait up to 5 minutes
            logging.info("Phone confirmation successful.")
        except Exception as e:
            logging.error("Phone confirmation timed out or failed: %s", e)
            raise RuntimeError("Phone confirmation required but not completed.")

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
