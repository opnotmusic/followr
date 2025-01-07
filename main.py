import os
import random
import logging
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Base comments in different languages
base_comments = {
    "english": [
        "Amazing post, @{username}! 🔥👽👽👽",
        "Great content, keep it up, @{username}! 🚀👽👽👽",
        "Love this, @{username}! 💗ྀི👽👽👽",
        "So inspiring, @{username}! 🌟👽👽👽",
        "Wow, just wow, @{username}! 👽👽👽🔥",
        "This made my day, @{username}! 👽👽👽🌌",
        "Totally agree, @{username}! 👽👽👽",
        "Brilliant work, @{username}! 👽👽👽",
    ],
    "spanish": [
        "¡Increíble publicación, @{username}! 🔥👽👽👽",
        "¡Gran contenido, sigue así, @{username}! 🚀👽👽👽",
        "¡Me encanta esto, @{username}! 💗ྀི👽👽👽",
        "¡Tan inspirador, @{username}! 🌟👽👽👽",
        "¡Wow, simplemente wow, @{username}! 👽👽👽🔥",
        "¡Esto me hizo el día, @{username}! 👽👽👽🌌",
        "¡Totalmente de acuerdo, @{username}! 👽👽👽",
        "¡Trabajo brillante, @{username}! 👽👽👽",
    ],
}

# Emoji pool for comment variations
emoji_pool = [
    "🔥", "👽", "🌟", "🌌", "🚀", "💫", "✨", "💡", "👏", "💥", "🌍", "😎"
]

# Sad-related keywords
sad_keywords = [
    "sad", "depressed", "lonely", "grief", "cry", "heartbroken", "mourning",
    "loss", "upset", "broken", "hurt", "pain", "tears", "alone", "#sad",
    "triste", "deprimido", "solitario", "pena", "llorar", "corazón roto",
    "duelo", "perdida", "dolor", "lágrimas", "solo"
]

class SocialMediaBot:
    def __init__(self):
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")
        self.target = os.getenv("TARGET_ACCOUNT", "example_target")
        if not self.username or not self.password:
            raise ValueError("Missing Instagram credentials! Set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in your .env file.")

        # Interaction limits
        self.max_comments = int(10 * 0.85)  # Limit to 85% of platform restrictions
        self.comments_pool = self.generate_all_comments("example_user")

    def generate_all_comments(self, username):
        all_comments = {}
        for language, comments in base_comments.items():
            updated_comments = [comment.replace("{username}", username) for comment in comments]
            all_comments[language] = self.generate_variations(updated_comments, 100)  # Generate 100 variations per language
        return all_comments

    def generate_variations(self, base_comments, count):
        variations = set()
        while len(variations) < count:
            for comment in base_comments:
                random_emojis = " ".join(random.choices(emoji_pool, k=random.randint(2, 4)))
                variations.add(f"{comment} {random_emojis}")
                if len(variations) >= count:
                    break
        return list(variations)

    def is_sad_post(self, post_text):
        lower_text = post_text.lower()
        return any(keyword in lower_text for keyword in sad_keywords)

    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            try:
                self.login(page)
                self.interact_with_posts(page)
            except Exception as e:
                logging.error(f"Error during bot execution: {e}")
            finally:
                browser.close()

    def login(self, page):
        logging.info("Logging into Instagram...")
        page.goto("https://www.instagram.com/accounts/login/")
        page.fill("input[name='username']", self.username)
        page.fill("input[name='password']", self.password)
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        logging.info("Login successful.")

    def interact_with_posts(self, page):
        logging.info(f"Navigating to target account: @{self.target}")
        page.goto(f"https://www.instagram.com/{self.target}/")
        page.wait_for_load_state("networkidle")

        post_links = page.locator("article a").evaluate_all("links => links.map(link => link.href)")
        logging.info(f"Found {len(post_links)} posts to interact with.")

        comments_count = 0
        for link in post_links:
            if comments_count >= self.max_comments:
                break

            page.goto(link)
            page.wait_for_load_state("networkidle")
            post_text = page.locator("article").text_content()

            if self.is_sad_post(post_text):
                logging.info("Sad post detected, skipping comment.")
                continue

            try:
                comment = random.choice(self.comments_pool["english"])
                page.fill("textarea", comment)
                page.click("button:has-text('Post')")
                comments_count += 1
                logging.info(f"Commented on post {comments_count}/{self.max_comments}: {comment}")
                page.wait_for_timeout(random.randint(1000, 3000))
            except Exception as e:
                logging.warning(f"Failed to comment on post: {e}")

if __name__ == "__main__":
    try:
        bot = SocialMediaBot()
        bot.run()
    except Exception as e:
        logging.error(f"Bot execution failed: {e}")
