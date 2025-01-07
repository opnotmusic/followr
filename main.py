import os
import json
import sys
import logging
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from cryptography.fernet import Fernet
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
        self.target = os.getenv('TARGET_ACCOUNT', 'davidguetta')

        if not self.username or not self.password:
            raise ValueError("Missing Instagram credentials! Set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in secrets.")

        # Interaction limits
        self.max_follows = int(30 * 0.85)  # 30 is Instagram's general limit
        self.max_likes = int(20 * 0.85)  # Adjusted for likes
        self.max_comments = int(10 * 0.85)  # Adjusted for comments

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

        # Log file to track interactions
        self.interaction_log_path = "interaction_log.json"
        self.interaction_log = self._load_interaction_log()

    def _load_interaction_log(self):
        if os.path.exists(self.interaction_log_path):
            with open(self.interaction_log_path, "r") as f:
                return json.load(f)
        return {"liked_posts": [], "commented_posts": [], "followed_users": []}

    def _save_interaction_log(self):
        with open(self.interaction_log_path, "w") as f:
            json.dump(self.interaction_log, f)

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
                self.follow_users(page)
            except Exception as e:
                logging.error("Error: %s", str(e))
            finally:
                self._save_interaction_log()
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

        # Get post links
        post_links = page.locator(post_selectors).evaluate_all("links => links.map(link => link.href)")
        logging.info("Found %d posts to interact with.", len(post_links))

        likes_count = 0
        comments_count = 0

        for link in post_links:
            if likes_count >= self.max_likes and comments_count >= self.max_comments:
                break

            # Skip already interacted posts
            if link in self.interaction_log["liked_posts"] or link in self.interaction_log["commented_posts"]:
                logging.info("Skipping already interacted post: %s", link)
                continue

            page.goto(link)
            page.wait_for_load_state("networkidle")

            # Like the post
            if random.choice([True, False]) and likes_count < self.max_likes:
                try:
                    like_button = page.locator("svg[aria-label='Like']").nth(0)
                    if like_button:
                        like_button.click()
                        likes_count += 1
                        self.interaction_log["liked_posts"].append(link)
                        logging.info("Liked post %d/%d: %s", likes_count, self.max_likes, link)
                        page.wait_for_timeout(random.randint(500, 2000))
                except Exception as e:
                    logging.warning("Failed to like post: %s", str(e))

            # Comment on the post
            if random.choice([True, False]) and comments_count < self.max_comments:
                try:
                    comment = random.choice(self.comments_pool)
                    page.fill("textarea", comment)
                    page.click("button:has-text('Post')")
                    comments_count += 1
                    self.interaction_log["commented_posts"].append(link)
                    logging.info("Commented on post %d/%d: %s", comments_count, self.max_comments, comment)
                    page.wait_for_timeout(random.randint(500, 2000))
                except Exception as e:
                    logging.warning("Failed to comment on post: %s", str(e))

            # Pause randomly to mimic human behavior
            page.wait_for_timeout(random.randint(1000, 3000))

    def follow_users(self, page):
        logging.info("Finding and following users...")
        page.goto(f"https://www.instagram.com/{self.target}/followers/", timeout=15000)
        page.wait_for_load_state("networkidle")

        # Scroll to load more followers
        scroll_count = 0
        while scroll_count < 5:  # Adjust based on testing
            page.evaluate("window.scrollBy(0, window.innerHeight)")
            page.wait_for_timeout(random.randint(1000, 2000))
            scroll_count += 1

        follow_buttons = page.locator("button:has-text('Follow')")
        follows_count = 0

        for i in range(follow_buttons.count()):
            if follows_count >= self.max_follows:
                break
            try:
                button = follow_buttons.nth(i)
                username = button.evaluate("el => el.closest('div').querySelector('a').href")
                if username in self.interaction_log["followed_users"]:
                    logging.info("Already followed user: %s", username)
                    continue

                if button.is_visible():
                    button.click()
                    follows_count += 1
                    self.interaction_log["followed_users"].append(username)
                    logging.info("Followed %d/%d users: %s", follows_count, self.max_follows, username)
                    page.wait_for_timeout(random.randint(500, 1500))
            except Exception as e:
                logging.warning("Failed to follow a user: %s", str(e))

if __name__ == "__main__":
    try:
        bot = SocialMediaBot()
        bot.run()
    except Exception as e:
        logging.error("Bot failed: %s", str(e))
        sys.exit(1)
