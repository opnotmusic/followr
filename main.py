import os
import random
import logging
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import sqlite3
from datetime import datetime, timedelta
from telegram import Bot
import secrets

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Securely store sensitive information using encryption
class SecureStorage:
    def __init__(self):
        self.key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
        self.cipher = Fernet(self.key)
        self.store_key()

    def store_key(self):
        if not os.path.exists(".secure_key"):  # Save the encryption key securely
            with open(".secure_key", "wb") as key_file:
                key_file.write(self.key)

    def encrypt(self, data):
        return self.cipher.encrypt(data.encode())

    def decrypt(self, encrypted_data):
        return self.cipher.decrypt(encrypted_data).decode()

class SocialMediaBot:
    def __init__(self):
        self.credentials = {
            "instagram": {
                "username": os.getenv("INSTAGRAM_USERNAME"),
                "password": os.getenv("INSTAGRAM_PASSWORD")
            },
        }
        self.targets = {
            "instagram": os.getenv("INSTAGRAM_TARGET", "example_target")
        }
        self.platforms = ["instagram"]
        self.default_language = "english"
        self.db_connection = sqlite3.connect("interactions.db")
        self.init_database()
        self.secure_storage = SecureStorage()

        # Store and encrypt the initial Telegram bot token
        initial_token = "7583008741:AAFlZm_nDZwt78XaxBZ71OBdwuzz354tfGM"
        self.telegram_bot_token = self.secure_storage.encrypt(initial_token)
        self.telegram_chat_id = self.secure_storage.encrypt(os.getenv("TELEGRAM_CHAT_ID"))
        self.wallet_address = self.secure_storage.encrypt(os.getenv("WALLET_ADDRESS"))

        # Default admin-configurable logo
        self.logo_path = "default_logo.png"

    def init_database(self):
        cursor = self.db_connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_limits (
                platform TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                daily_limit INTEGER NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS app_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opened_count INTEGER NOT NULL DEFAULT 0,
                last_opened TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memberships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                membership_type TEXT NOT NULL,
                price REAL NOT NULL,
                next_billing_date TIMESTAMP NOT NULL DEFAULT (DATETIME('now', '+1 month')),
                access_code TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS earnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                amount REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                membership_type TEXT NOT NULL,
                base_price REAL NOT NULL
            )
            """
        )
        self.db_connection.commit()
        self.init_default_settings()

    def init_default_settings(self):
        # Initialize default membership settings
        cursor = self.db_connection.cursor()
        default_settings = [
            ("basic", 10),
            ("standard", 20),
            ("premium", 30)
        ]
        for membership_type, price in default_settings:
            cursor.execute(
                "INSERT OR IGNORE INTO admin_settings (membership_type, base_price) VALUES (?, ?)",
                (membership_type, price)
            )
        self.db_connection.commit()

    def update_logo(self, new_logo_path):
        if os.path.exists(new_logo_path):
            self.logo_path = new_logo_path
            logging.info(f"Updated app logo to: {new_logo_path}")
        else:
            logging.error(f"Logo file not found: {new_logo_path}")

    def update_telegram_bot_token(self, new_token):
        self.telegram_bot_token = self.secure_storage.encrypt(new_token)
        logging.info("Telegram bot token updated successfully.")

    def update_membership_price(self, membership_type, new_price):
        cursor = self.db_connection.cursor()
        cursor.execute(
            "UPDATE admin_settings SET base_price = ? WHERE membership_type = ?",
            (new_price, membership_type)
        )
        self.db_connection.commit()
        logging.info(f"Updated {membership_type} membership price to ${new_price:.2f}.")

    def get_membership_price(self, membership_type):
        cursor = self.db_connection.cursor()
        cursor.execute(
            "SELECT base_price FROM admin_settings WHERE membership_type = ?",
            (membership_type,)
        )
        result = cursor.fetchone()
        return result[0] if result else None

    def create_membership(self, user_id, membership_type):
        cursor = self.db_connection.cursor()
        base_price = self.get_membership_price(membership_type)
        if base_price is None:
            logging.error(f"Membership type {membership_type} does not exist.")
            return

        price = base_price * 1.25  # 25% boost
        access_code = self.generate_unique_code()
        cursor.execute(
            "INSERT INTO memberships (user_id, membership_type, price, access_code) VALUES (?, ?, ?, ?)",
            (user_id, membership_type, price, access_code)
        )
        self.db_connection.commit()
        self.send_code_to_telegram(access_code)
        logging.info(f"Created {membership_type} membership for user {user_id} at ${price:.2f}. Access Code: {access_code}")

    def generate_unique_code(self):
        return secrets.token_hex(4)  # 8-character unique code

    def send_code_to_telegram(self, code):
        decrypted_chat_id = self.secure_storage.decrypt(self.telegram_chat_id)
        decrypted_token = self.secure_storage.decrypt(self.telegram_bot_token)
        bot = Bot(token=decrypted_token)
        bot.send_message(chat_id=decrypted_chat_id, text=f"Generated Membership Access Code: {code}")
        logging.info("Access code sent to Telegram.")

    def process_recurring_payments(self):
        cursor = self.db_connection.cursor()
        cursor.execute(
            "SELECT id, user_id, price, next_billing_date FROM memberships WHERE next_billing_date <= DATETIME('now')"
        )
        due_memberships = cursor.fetchall()
        for membership in due_memberships:
            membership_id, user_id, price, next_billing_date = membership
            self.record_earning(user_id, price)
            new_billing_date = datetime.strptime(next_billing_date, "%Y-%m-%d %H:%M:%S") + timedelta(days=30)
            cursor.execute(
                "UPDATE memberships SET next_billing_date = ? WHERE id = ?",
                (new_billing_date.strftime("%Y-%m-%d %H:%M:%S"), membership_id)
            )
        self.db_connection.commit()
        logging.info(f"Processed {len(due_memberships)} recurring payments.")

    def record_earning(self, user_id, amount):
        cursor = self.db_connection.cursor()
        cursor.execute(
            "INSERT INTO earnings (user_id, amount) VALUES (?, ?)",
            (user_id, amount)
        )
        self.db_connection.commit()
        logging.info(f"Recorded earning of ${amount:.2f} for user {user_id}.")

    def view_earnings(self):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT SUM(amount) FROM earnings")
        total_earnings = cursor.fetchone()[0] or 0
        logging.info(f"Total Earnings from Cloud Services: ${total_earnings:.2f}")

    def display_admin_wallet(self):
        decrypted_wallet = self.secure_storage.decrypt(self.wallet_address)
        logging.info(f"Admin Wallet Address: {decrypted_wallet}")

    def validate_telegram_bot(self):
        decrypted_chat_id = self.secure_storage.decrypt(self.telegram_chat_id)
        logging.info(f"Telegram Bot validated for Chat ID: {decrypted_chat_id}")

    def run(self):
        self.check_and_offer_cloud_service()
        base_limits = {"instagram": 200}
        for platform in self.platforms:
            limit = self.get_daily_limit(platform, base_limits[platform])
            logging.info(f"Starting {platform.capitalize()} interactions (limit: {limit})")
            try:
                if platform == "instagram":
                    self.instagram_interact(limit)
            except Exception as e:
                logging.error(f"Error with {platform.capitalize()}: {e}")
        self.process_recurring_payments()
        self.display_admin_wallet()
        self.validate_telegram_bot()

    def instagram_interact(self, limit):
        logging.info(f"Interacting with Instagram posts (limit: {limit})")
        for i in range(limit):
            comment = self.get_comment("instagram", self.default_language)
            self.log_interaction("instagram", f"Commented: {comment}")

if __name__ == "__main__":
    bot = SocialMediaBot()
    bot.run()
