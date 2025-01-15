import os
import random
import logging
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from transformers import pipeline
from playwright.sync_api import sync_playwright
from telegram import Bot
from discord.ext import commands
import firebase_admin
from firebase_admin import credentials, auth
from flask import Flask, request, jsonify

# Initialize Flask app
app = Flask(__name__)

# Load Firebase Admin credentials (service account key JSON file)
cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Sentiment analysis pipeline
sentiment_analyzer = pipeline("sentiment-analysis")

# Database setup
DB_PATH = "interactions.db"

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_url TEXT NOT NULL,
            username TEXT NOT NULL,
            comment TEXT,
            sentiment TEXT,
            engagement_score REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()

init_database()

# Endpoint to verify Firebase token
@app.route('/verify-token', methods=['POST'])
def verify_token():
    token = request.json.get('idToken')  # Token sent from client
    if not token:
        return jsonify({"status": "error", "message": "No token provided"}), 400

    try:
        # Verify the token
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        return jsonify({
            "status": "success",
            "uid": user_id
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 401

class SocialMediaBot:
    def __init__(self):
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")
        self.target = os.getenv("TARGET_ACCOUNT", "example_target")
        if not self.username or not self.password:
            raise ValueError("Missing Instagram credentials! Set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in your .env file.")

        # Telegram setup
        self.telegram_bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

        # Discord setup
        self.discord_bot = commands.Bot(command_prefix="!")

        # Interaction limits
        self.max_comments = int(10 * 0.85)  # Limit to 85% of platform restrictions
        self.max_likes = int(100 * 0.90)  # Limit to 90% of platform restrictions
        self.max_follows = int(50 * 0.75)  # Limit to 75% of platform restrictions
        self.comments_pool = self.generate_all_comments("example_user")

    def generate_all_comments(self, username):
        base_comments = {
            "english": [
                "Amazing post, @{username}! 🔥👽👽👽",
                "Great content, keep it up, @{username}! 🚀👽👽👽",
                "Love this, @{username}! 💗ྀི👽👽👽",
                "So inspiring, @{username}! 🌟👽👽👽",
                "Wow, just wow, @{username}! 👽👽👽🔥",
                "This made my day, @{username}! 👽👽👽🌌",
            ]
        }
        all_comments = {}
        for language, comments in base_comments.items():
            updated_comments = [comment.replace("{username}", username) for comment in comments]
            all_comments[language] = updated_comments
        return all_comments

    def analyze_sentiment(self, text):
        result = sentiment_analyzer(text)[0]
        return result['label'], result['score']

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

if __name__ == "__main__":
    # Run Flask app for token verification
    logging.info("Starting Flask app for token verification...")
    app.run(debug=True, port=5000)

    # Initialize and run the social media bot
    bot = SocialMediaBot()
    bot.run()
