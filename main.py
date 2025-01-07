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

        self.max_interactions = {
            'likes': 20,  # Max likes per session
            'comments': 10,  # Max comments per session
            'follows': 30,  # Max follows per session
        }

        self.comments_pool = [
            "Amazing post! 👏",
            "Great content, keep it up! 🚀",
            "Love this! ❤️",
            "So inspiring! 🌟",
            "Wow, just wow! 🔥",
            "This made my day! 😊",
            "Totally agree! 🙌",
            "Brilliant work! 💡",
        ]

    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            try:
                logging.info("Starting bot...")
                self.login(page)
                self.interact_with_posts(page)
            except Exception as e:
                logging.error("Error: %s", str(e))
            finally:
                browser.close()

    def login(self, page):
        logging.info("Logging into Instagram...")
        page.goto("https://www.instagram.com/accounts/login/", timeout=15000)
        page.fill("input[name='username']", self.username)
        page.fill("input[name='password']", self.password)
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        logging.info("Login successful.")

    def interact_with_posts(self, page):
        logging.info("Navigating to target account: %s", self.target)
        page.goto(f"https://www.instagram.com/{self.target}/", timeout=15000)
        page.wait_for_load_state("networkidle")
        post_selectors = "article a"

        # Open posts to interact
        post_links = page.locator(post_selectors).evaluate_all("links => links.map(link => link.href)")
        logging.info("Found %d posts to interact with.", len(post_links))

        likes_count = 0
        comments_count = 0

        for link in post_links:
            if likes_count >= self.max_interactions['likes'] and comments_count >= self.max_interactions['comments']:
                break

            page.goto(link)
            page.wait_for_load_state("networkidle")

            # Like the post
            if random.choice([True, False]) and likes_count < self.max_interactions['likes']:
                try:
                    like_button = page.locator("svg[aria-label='Like']").nth(0)
                    if like_button:
                        like_button.click()
                        likes_count += 1
                        logging.info("Liked post %d/%d", likes_count, self.max_interactions['likes'])
                        page.wait_for_timeout(random.randint(500, 2000))
                except Exception as e:
                    logging.warning("Failed to like post: %s", str(e))

            # Comment on the post
            if random.choice([True, False]) and comments_count < self.max_interactions['comments']:
                try:
                    comment = random.choice(self.comments_pool)
                    page.fill("textarea", comment)
                    page.click("button:has-text('Post')")
                    comments_count += 1
                    logging.info("Commented on post %d/%d: %s", comments_count, self.max_interactions['comments'], comment)
                    page.wait_for_timeout(random.randint(500, 2000))
                except Exception as e:
                    logging.warning("Failed to comment on post: %s", str(e))

            # Pause randomly to mimic human behavior
            page.wait_for_timeout(random.randint(1000, 3000))

if __name__ == "__main__":
    try:
        bot = SocialMediaBot()
        bot.run()
    except Exception as e:
        logging.error("Bot failed: %s", str(e))
        sys.exit(1)
