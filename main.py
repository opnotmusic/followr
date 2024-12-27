import os
import json
import sys
from playwright.sync_api import sync_playwright
import time
from datetime import datetime
import random

class SocialMediaBot:
    def __init__(self):
        self.credentials = {
            'instagram': {
                'username': os.environ.get('INSTAGRAM_USERNAME'),
                'password': os.environ.get('INSTAGRAM_PASSWORD'),
                'target': os.environ.get('INSTAGRAM_TARGET', 'davidguetta'),
                'max_follows': 133
            },
            'threads': {
                'username': os.environ.get('THREADS_USERNAME'),
                'password': os.environ.get('THREADS_PASSWORD'),
                'target': os.environ.get('THREADS_TARGET', 'davidguetta'),
                'max_follows': 100
            },
            'twitter': {
                'username': os.environ.get('TWITTER_USERNAME'),
                'password': os.environ.get('TWITTER_PASSWORD'),
                'target': os.environ.get('TWITTER_TARGET', 'davidguetta'),
                'max_follows': 400
            },
            'tiktok': {
                'username': os.environ.get('TIKTOK_USERNAME'),
                'password': os.environ.get('TIKTOK_PASSWORD'),
                'target': os.environ.get('TIKTOK_TARGET', 'davidguetta'),
                'max_follows': 200
            }
        }
        
        self.platform_urls = {
            'instagram': 'https://www.instagram.com/accounts/login/',
            'threads': 'https://www.threads.net/login',
            'twitter': 'https://twitter.com/i/flow/login',
            'tiktok': 'https://www.tiktok.com/login'
        }
        
        self.follow_counts = {platform: 0 for platform in self.credentials.keys()}

    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            for platform in self.credentials.keys():
                if not all([self.credentials[platform]['username'], 
                          self.credentials[platform]['password']]):
                    print(f"Skipping {platform} - missing credentials")
                    continue
                    
                print(f"\nStarting {platform} automation...")
                page = context.new_page()
                
                try:
                    self.login(page, platform)
                    self.find_followers(page, platform)
                    self.follow_users(page, platform)
                except Exception as e:
                    print(f"Error on {platform}: {str(e)}")
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    page.screenshot(path=f"{platform}_error_{timestamp}.png")
                finally:
                    page.close()
            
            context.close()
            browser.close()

    def login(self, page, platform):
        print(f"Logging into {platform}...")
        
        # Check for cached session
        cache_file = f"{platform}_session_cache.json"
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                session_data = json.load(f)
                page.context.add_cookies(session_data.get('cookies', []))
                return

        page.goto(self.platform_urls[platform])
        page.wait_for_load_state("networkidle")
        
        if platform == 'instagram' or platform == 'threads':
            self._instagram_login(page, platform)
        elif platform == 'twitter':
            self._twitter_login(page)
        elif platform == 'tiktok':
            self._tiktok_login(page)
            
        # Cache session
        cookies = page.context.cookies()
        with open(cache_file, 'w') as f:
            json.dump({'cookies': cookies}, f)

    def _instagram_login(self, page, platform):
        try:
            page.get_by_role("button", name="Allow all cookies").click()
        except:
            pass
            
        creds = self.credentials[platform]
        page.fill("input[name='username']", creds['username'])
        page.fill("input[name='password']", creds['password'])
        page.click("button[type='submit']")
        
        self._handle_2fa(page)
        self._handle_dialogs(page)

    def _twitter_login(self, page):
        creds = self.credentials['twitter']
        page.fill("input[autocomplete='username']", creds['username'])
        page.click("span:has-text('Next')")
        page.fill("input[name='password']", creds['password'])
        page.click("div[data-testid='LoginForm_Login_Button']")
        
        self._handle_2fa(page)

    def _tiktok_login(self, page):
        creds = self.credentials['tiktok']
        page.click("button:has-text('Use phone / email / username')")
        page.click("a:has-text('Log in with email or username')")
        page.fill("input[name='username']", creds['username'])
        page.fill("input[type='password']", creds['password'])
        page.click("button[type='submit']")
        
        self._handle_2fa(page)

    def _handle_2fa(self, page):
        try:
            if page.query_selector("input[name='verificationCode']"):
                code = input("Enter 2FA code: ")
                page.fill("input[name='verificationCode']", code)
                page.click("button[type='submit']")
        except:
            pass

    def _handle_dialogs(self, page):
        dialogs = {
            "Not Now": ["button:has-text('Not Now')", "button:has-text('Skip')", "button:has-text('Maybe Later')"],
            "Cancel": ["button:has-text('Cancel')", "button:has-text('Close')"]
        }
        
        for dialog_type, selectors in dialogs.items():
            for selector in selectors:
                try:
                    button = page.query_selector(selector)
                    if button:
                        button.click()
                        print(f"Handled {dialog_type} dialog")
                        page.wait_for_timeout(1000)
                except:
                    continue

    def find_followers(self, page, platform):
        target = self.credentials[platform]['target']
        print(f"Finding followers for {target} on {platform}...")
        
        if platform == 'instagram' or platform == 'threads':
            page.goto(f"https://www.instagram.com/{target}/")
        elif platform == 'twitter':
            page.goto(f"https://twitter.com/{target}/followers")
        elif platform == 'tiktok':
            page.goto(f"https://www.tiktok.com/@{target}/followers")
            
        page.wait_for_load_state("networkidle")
        
        # Platform-specific selectors for followers
        selectors = {
            'instagram': ["a:has-text('followers')", f"a[href='/{target}/followers/']"],
            'threads': ["a:has-text('followers')", f"a[href='/{target}/followers/']"],
            'twitter': ["[data-testid='followers']"],
            'tiktok': ["span:has-text('Followers')"]
        }
        
        for selector in selectors.get(platform, []):
            try:
                page.click(selector)
                break
            except:
                continue
                
        page.wait_for_timeout(2000)
        self._scroll_followers(page, platform)

    def _scroll_followers(self, page, platform):
        max_follows = self.credentials[platform]['max_follows']
        scroll_count = min(10, (max_follows // 12) + 2)
        
        for i in range(scroll_count):
            page.keyboard.press('PageDown')
            page.wait_for_timeout(random.uniform(500, 1000))
            print(f"Scroll {i + 1}/{scroll_count}")

    def follow_users(self, page, platform):
        max_follows = self.credentials[platform]['max_follows']
        
        # Platform-specific follow button selectors
        follow_selectors = {
            'instagram': "button:has-text('Follow')",
            'threads': "button:has-text('Follow')",
            'twitter': "[data-testid='follow']",
            'tiktok': "button:has-text('Follow')"
        }
        
        follow_buttons = page.locator(follow_selectors[platform])
        count = min(follow_buttons.count(), max_follows)
        
        print(f"Found {count} accounts to follow on {platform}")
        
        for i in range(count):
            if self.follow_counts[platform] >= max_follows:
                break
                
            try:
                button = follow_buttons.nth(i)
                if button.is_visible():
                    page.wait_for_timeout(random.uniform(500, 1500))
                    button.click()
                    self.follow_counts[platform] += 1
                    print(f"Followed {self.follow_counts[platform]}/{max_follows} on {platform}")
                    self._handle_dialogs(page)
            except Exception as e:
                print(f"Error following user on {platform}: {str(e)}")
                continue

def main():
    try:
        bot = SocialMediaBot()
        bot.run()
    except Exception as e:
        print(f"Bot failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
