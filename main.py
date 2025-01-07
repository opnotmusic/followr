import os
import json
import sys
import logging
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from cryptography.fernet import Fernet
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import random

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
                finally:
                    page.close()
                    context.close()
                    browser.close()

        with ThreadPoolExecutor() as executor:
            executor.map(process_platform, self.max_follows.keys())

    def login(self, page, platform):
        cache_file = f"{platform}_session_cache.json"
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cookies = self.decrypt_cookies(f.read())
                    page.context.add_cookies(cookies.get('cookies', []))
                logging.info(f"Loaded session cookies for {platform}.")
                return
            except Exception as e:
                logging.warning(f"Failed to load session cookies for {platform}: {e}")

        self._perform_platform_login(page, platform)

        cookies = page.context.cookies()
        with open(cache_file, 'w') as f:
            f.write(self.encrypt_cookies({'cookies': cookies}))
        logging.info(f"Session cookies saved for {platform}.")

    def encrypt_cookies(self, cookies):
        return fernet.encrypt(json.dumps(cookies).encode()).decode()

    def decrypt_cookies(self, encrypted):
        return json.loads(fernet.decrypt(encrypted.encode()).decode())

    def _perform_platform_login(self, page, platform):
        logging.info(f"Logging into {platform}...")
        if platform == "instagram":
            self._perform_instagram_login(page)
        else:
            self._perform_google_login(page, platform)

    def _perform_instagram_login(self, page):
        page.goto(self.platform_urls['instagram'], timeout=15000)
        page.fill("input[name='username']", self.username)
        page.fill("input[name='password']", self.password)
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")

    def _perform_google_login(self, page, platform):
        logging.info(f"Logging into {platform} using Google...")
        page.goto(self.platform_urls[platform], timeout=15000)
        # Add more Google login details if required for other platforms.

    def find_followers(self, page, platform):
        logging.info(f"Finding followers on {platform}...")
        page.goto(self.platform_urls[platform], timeout=15000)
        page.wait_for_load_state("networkidle")

    def follow_users(self, page, platform):
        logging.info(f"Following users on {platform}...")
        # Add detailed follow user logic.

if __name__ == "__main__":
    try:
        bot = SocialMediaBot()
        bot.run()
    except Exception as e:
        logging.error(f"Bot failed: {str(e)}")
        sys.exit(1)
