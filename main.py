import os
import sqlite3
import logging
import datetime
import requests
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class SecureStorage:
    def __init__(self):
        self.key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
        self.cipher = Fernet(self.key)
        self.store_key()

    def store_key(self):
        if not os.path.exists(".secure_key"):
            with open(".secure_key", "wb") as key_file:
                key_file.write(self.key)

    def encrypt(self, data):
        return self.cipher.encrypt(data.encode())

    def decrypt(self, encrypted_data):
        return self.cipher.decrypt(encrypted_data).decode()


class SocialMediaBot:
    def __init__(self):
        self.db_connection = sqlite3.connect("interactions.db")
        self.init_database()
        self.secure_storage = SecureStorage()

        # Load Telegram credentials
        self.telegram_bot_token = self.get_telegram_token()
        self.telegram_chat_id = self.get_telegram_chat_id()

    def init_database(self):
        """Initialize database tables."""
        cursor = self.db_connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                is_super_user INTEGER DEFAULT 0,
                promo_image_url TEXT,
                last_service_date TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                service TEXT NOT NULL,
                price REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        self.db_connection.commit()

    def get_telegram_token(self):
        """Retrieve the Telegram bot token from secure storage."""
        # Example: Stored as environment variable
        return os.getenv("TELEGRAM_BOT_TOKEN", None)

    def get_telegram_chat_id(self):
        """Retrieve the Telegram chat ID from secure storage."""
        # Example: Stored as environment variable
        return os.getenv("TELEGRAM_CHAT_ID", None)

    def register_user(self, username):
        """Register a new user."""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            logging.info(f"User {username} already exists.")
            return "User already exists."

        cursor.execute(
            "INSERT INTO users (username) VALUES (?)",
            (username,)
        )
        self.db_connection.commit()
        logging.info(f"User {username} registered successfully.")
        return "User registered successfully."

    def set_super_user(self, username, is_super_user):
        """Promote or demote a user to super user."""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            logging.error(f"User {username} not found.")
            return f"User {username} not found."

        cursor.execute(
            "UPDATE users SET is_super_user = ? WHERE username = ?",
            (1 if is_super_user else 0, username)
        )
        self.db_connection.commit()
        logging.info(f"User {username} updated to super user: {is_super_user}.")
        return f"User {username} updated successfully."

    def add_service(self, username, service, price):
        """Log a service acquisition and notify the admin."""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            logging.error(f"User {username} not found.")
            return f"User {username} not found."

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            INSERT INTO services (username, service, price, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (username, service, price, timestamp)
        )
        self.db_connection.commit()
        logging.info(f"Service {service} added for user {username} at {price}.")
        self.send_admin_notification(username, service, price)
        return f"Service {service} logged successfully."

    def send_admin_notification(self, username, service, price):
        """Send a notification to the admin when a service is acquired."""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logging.error("Telegram bot credentials are not set.")
            return

        message = (
            f"🔔 New Service Acquired!\n"
            f"👤 User: {username}\n"
            f"💲 Price: ${price:.2f}\n"
            f"📄 Service: {service}\n"
        )
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {"chat_id": self.telegram_chat_id, "text": message}

        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                logging.info("Admin notification sent successfully.")
            else:
                logging.error(f"Failed to send notification: {response.text}")
        except Exception as e:
            logging.error(f"Error sending Telegram notification: {e}")

    def admin_console(self):
        """Admin interface for managing users and services."""
        while True:
            print("\n--- Admin Console ---")
            print("1. Register User")
            print("2. Set Super User")
            print("3. Add Service")
            print("4. Exit")
            choice = input("Enter your choice: ")

            if choice == "1":
                username = input("Enter username to register: ")
                print(self.register_user(username))
            elif choice == "2":
                username = input("Enter username to update: ")
                is_super_user = input("Set as super user? (yes/no): ").strip().lower() == "yes"
                print(self.set_super_user(username, is_super_user))
            elif choice == "3":
                username = input("Enter username: ")
                service = input("Enter service name: ")
                price = float(input("Enter service price: "))
                print(self.add_service(username, service, price))
            elif choice == "4":
                print("Exiting admin console...")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    bot = SocialMediaBot()
    print("\n--- Social Media Bot ---")
    bot.admin_console()
