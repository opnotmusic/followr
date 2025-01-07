import os
import random
import logging
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import matplotlib.pyplot as plt

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Base comments in different languages
base_comments = {
    "general": {
        "english": [
            "Amazing post! 🔥👽👽👽",
            "Great content, keep it up! 🚀👽👽👽",
            "Love this! 💗ྀི👽👽👽",
            "So inspiring! 🌟👽👽👽",
            "Wow, just wow! 👽👽👽🔥",
            "This made my day! 👽👽👽🌌",
            "Totally agree! 👽👽👽",
            "Brilliant work! 👽👽👽",
        ],
        "spanish": [
            "¡Increíble publicación! 🔥👽👽👽",
            "¡Gran contenido, sigue así! 🚀👽👽👽",
            "¡Me encanta esto! 💗ྀི👽👽👽",
            "¡Tan inspirador! 🌟👽👽👽",
            "¡Wow, simplemente wow! 👽👽👽🔥",
            "¡Esto me hizo el día! 👽👽👽🌌",
            "¡Totalmente de acuerdo! 👽👽👽",
            "¡Trabajo brillante! 👽👽👽",
        ],
    },
    "platform_specific": {
        "soundcloud": [
            "Great track! 🎵🔥",
            "This is on repeat! 🎧✨",
            "Amazing vibes! 🎶👽",
        ],
        "twitter": [
            "Interesting take! 🐦🔥",
            "Totally agree with this tweet! 👽✨",
            "Great insight, keep it up! 🌟💬",
        ],
    },
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
        self.credentials = {
            "instagram": {
                "username": os.getenv("INSTAGRAM_USERNAME"),
                "password": os.getenv("INSTAGRAM_PASSWORD")
            },
            "twitter": {
                "username": os.getenv("TWITTER_USERNAME"),
                "password": os.getenv("TWITTER_PASSWORD")
            },
            "soundcloud": {
                "username": os.getenv("SOUNDCLOUD_USERNAME"),
                "password": os.getenv("SOUNDCLOUD_PASSWORD")
            },
        }
        self.targets = {
            "instagram": os.getenv("INSTAGRAM_TARGET", "example_target"),
            "twitter": os.getenv("TWITTER_TARGET", "example_target"),
            "soundcloud": os.getenv("SOUNDCLOUD_TARGET", "example_artist"),
        }
        self.platforms = ["instagram", "twitter", "soundcloud"]
        self.max_comments = int(10 * 0.85)  # Limit to 85% of platform restrictions
        self.interaction_count = {platform: 0 for platform in self.platforms}

    def generate_all_comments(self, platform):
        username = self.targets[platform]
        base = base_comments["general"]
        platform_specific = base_comments.get("platform_specific", {}).get(platform, [])
        all_comments = {}

        for language, comments in base.items():
            updated_comments = [
                self.modify_comment(comment, username) for comment in comments
            ] + platform_specific
            all_comments[language] = self.generate_variations(updated_comments, 100)  # Generate 100 variations per language
        return all_comments

    def modify_comment(self, comment, username):
        # Randomly decide to include username or not
        if random.choice([True, False]):
            return comment.replace("@{username}", username)
        return comment.replace("@{username}", "")

    def generate_variations(self, base_comments, count):
        variations = set()
        while len(variations) < count:
            for comment in base_comments:
                random_emojis = " ".join(random.choices(emoji_pool, k=random.randint(2, 4)))
                variations.add(f"{comment} {random_emojis}".strip())
                if len(variations) >= count:
                    break
        return list(variations)

    def is_sad_post(self, post_text):
        lower_text = post_text.lower()
        return any(keyword in lower_text for keyword in sad_keywords)

    def run(self):
        for platform in self.platforms:
            try:
                logging.info(f"Starting interactions on {platform.capitalize()}...")
                if platform == "instagram":
                    self.instagram_interact()
                elif platform == "twitter":
                    self.twitter_interact()
                elif platform == "soundcloud":
                    self.soundcloud_interact()
                logging.info(f"Finished interactions on {platform.capitalize()}.")
            except Exception as e:
                logging.error(f"Error on {platform.capitalize()}: {e}")

        # Output interaction counts
        self.display_interaction_summary()

    def instagram_interact(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            try:
                self.instagram_login(page)
                # Simulate interactions
                self.interaction_count["instagram"] += 5  # Example increment
            except Exception as e:
                logging.error(f"Instagram interaction failed: {e}")
            finally:
                browser.close()

    def instagram_login(self, page):
        creds = self.credentials["instagram"]
        logging.info("Logging into Instagram...")
        page.goto("https://www.instagram.com/accounts/login/")
        page.fill("input[name='username']", creds["username"])
        page.fill("input[name='password']", creds["password"])
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        logging.info("Instagram login successful.")

    def twitter_interact(self):
        # Simulate interactions
        self.interaction_count["twitter"] += 3  # Example increment
        logging.info("Twitter interactions simulated.")

    def soundcloud_interact(self):
        # Simulate interactions
        self.interaction_count["soundcloud"] += 7  # Example increment
        logging.info("SoundCloud interactions simulated.")

    def display_interaction_summary(self):
        logging.info("Interaction Summary:")
        for platform, count in self.interaction_count.items():
            logging.info(f"{platform.capitalize()}: {count} interactions")

        # Generate and display statistics
        self.generate_statistics()

    def generate_statistics(self):
        platforms = list(self.interaction_count.keys())
        counts = list(self.interaction_count.values())

        # Plotting the statistics
        plt.figure(figsize=(10, 6))
        plt.bar(platforms, counts, color=['blue', 'orange', 'green'])
        plt.xlabel("Platforms")
        plt.ylabel("Number of Interactions")
        plt.title("Social Media Interactions per Platform")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.show()

if __name__ == "__main__":
    try:
        bot = SocialMediaBot()
        bot.run()
    except Exception as e:
        logging.error(f"Bot execution failed: {e}")
