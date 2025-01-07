import os
import random
import logging
import locale
import sqlite3
import requests
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from telegram import Bot

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

        # Load Telegram bot credentials
        initial_token = "7583008741:AAFlZm_nDZwt78XaxBZ71OBdwuzz354tfGM"
        self.telegram_bot_token = self.secure_storage.encrypt(initial_token)
        self.telegram_chat_id = self.secure_storage.encrypt(os.getenv("TELEGRAM_CHAT_ID"))

    def init_database(self):
        cursor = self.db_connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                activation_code TEXT NOT NULL,
                promo_image_url TEXT,
                behavior TEXT DEFAULT 'default'
            )
            """
        )
        self.db_connection.commit()

    def receive_activation_code(self, username, activation_code):
        """Process activation code and generate promotional image."""
        cursor = self.db_connection.cursor()

        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            logging.info(f"User {username} already activated.")
            return existing_user[3]  # Return existing promo image URL

        # Generate a promotional image
        promo_image_url = self.generate_dalle_image(
            f"A futuristic promotional poster featuring an alien theme for {username}'s activation. Modern and sleek design, emphasizing creativity and technology.",
            save_as=f"{username}_promo.png"
        )

        # Store user details in the database
        cursor.execute(
            "INSERT INTO users (username, activation_code, promo_image_url, behavior) VALUES (?, ?, ?, ?)",
            (username, activation_code, promo_image_url, "default")
        )
        self.db_connection.commit()
        logging.info(f"User {username} added with promo image URL: {promo_image_url}")
        return promo_image_url

    def generate_dalle_image(self, prompt, image_size="1024x1024", save_as=None):
        """Generate an image dynamically using OpenAI DALL·E API."""
        try:
            logging.info(f"Generating image with prompt: {prompt}")
            # Placeholder for OpenAI API integration
            response = requests.get(f"https://source.unsplash.com/random/800x600?{prompt.replace(' ', '+')}")
            if response.status_code == 200:
                image_url = response.url
                logging.info(f"Generated image URL: {image_url}")

                # Optionally save the image locally
                if save_as:
                    img_data = requests.get(image_url).content
                    with open(save_as, "wb") as handler:
                        handler.write(img_data)
                    logging.info(f"Image saved as: {save_as}")

                return image_url
        except Exception as e:
            logging.error(f"Error generating image: {e}")
            return None

    def render_user_interface(self, username):
        """Render the user interface with the promotional content."""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT promo_image_url FROM users WHERE username = ?", (username,))
        promo_image = cursor.fetchone()

        if promo_image:
            print(f"\n--- Welcome, {username}! ---")
            print(f"Your promotional image: {promo_image[0]}")
        else:
            print(f"No promotional content found for {username}.")

    def admin_console(self):
        """Admin interface for managing users and promotions."""
        while True:
            print("\n--- Admin Console ---")
            print("1. View Users")
            print("2. Change User Behavior")
            print("3. Exit")
            choice = input("Enter your choice: ")

            if choice == "1":
                self.view_users()
            elif choice == "2":
                username = input("Enter the username to modify: ")
                self.change_user_behavior(username)
            elif choice == "3":
                print("Exiting admin console...")
                break
            else:
                print("Invalid choice. Please try again.")

    def view_users(self):
        """Display all registered users."""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT username, promo_image_url, behavior FROM users")
        users = cursor.fetchall()
        print("\n--- Registered Users ---")
        for user in users:
            print(f"Username: {user[0]}, Promo Image: {user[1]}, Behavior: {user[2]}")
        print("-------------------------")

    def change_user_behavior(self, username):
        """Allow the admin to change a user's behavior."""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            print(f"User {username} not found.")
            return

        print(f"Current behavior for {username}: {user[4]}")
        print("Available behaviors:")
        print("1. Default")
        print("2. VIP")
        print("3. High Engagement Mode")
        print("4. Custom")
        choice = input("Select the new behavior: ")

        behaviors = {
            "1": "default",
            "2": "vip",
            "3": "high_engagement",
            "4": "custom"
        }
        new_behavior = behaviors.get(choice, "default")

        cursor.execute(
            "UPDATE users SET behavior = ? WHERE username = ?",
            (new_behavior, username)
        )
        self.db_connection.commit()
        print(f"Behavior for {username} updated to {new_behavior}.")


if __name__ == "__main__":
    bot = SocialMediaBot()
    username = input("Enter your username: ")
    activation_code = input("Enter your activation code: ")
    promo_image = bot.receive_activation_code(username, activation_code)
    if promo_image:
        bot.render_user_interface(username)
    bot.admin_console()
