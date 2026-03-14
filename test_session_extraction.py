"""Script to extract session from Playwright to requests."""

import time
import os
import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

def test_session_extraction():
    username = os.environ.get("AMD_USERNAME")
    password = os.environ.get("AMD_PASSWORD")
    
    if not username or not password:
        print("AMD_USERNAME or AMD_PASSWORD not set")
        return

    print(f"Starting session extraction for {username}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-http2"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)

        try:
            # Navigate to login
            url = "https://account.amd.com/en/forms/downloads/xef.html?filename=FPGAs_AdaptiveSoCs_Unified_2023.2_1013_2256_Lin64.bin"
            print(f"Navigating to {url}...")
            page.goto(url, wait_until="commit", timeout=120000)
            time.sleep(10)
            
            # Perform login
            print("Filling login form...")
            page.fill("input[name='identifier']", username)
            page.click("input[type='submit']")
            time.sleep(5)
            
            page.fill("input[name='credentials.passcode']", password)
            page.click("input[type='submit']")
            time.sleep(10)
            
            # Handle "Stay signed in?"
            try:
                if page.is_visible("#idSIButton9"):
                    page.click("#idSIButton9")
                    time.sleep(5)
            except:
                pass
                
            print(f"Current URL after login: {page.url}")
            
            # Extract cookies
            cookies = context.cookies()
            print(f"Extracted {len(cookies)} cookies")
            
            # Build requests session
            session = requests.Session()
            for cookie in cookies:
                session.cookies.set(
                    cookie['name'], 
                    cookie['value'], 
                    domain=cookie.get('domain'), 
                    path=cookie.get('path', '/')
                )
            
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            })
            
            # Verify session with a small request
            # Try to get the download page or similar
            test_url = "https://www.xilinx.com/support/download.html"
            print(f"Verifying session with request to {test_url}...")
            response = session.get(test_url, timeout=30)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                print("Session successfully exported and verified!")
            else:
                print(f"Verification failed with status {response.status_code}")
                
        except Exception as exc:
            print(f"Error during extraction: {exc}")
            page.screenshot(path="extraction-error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    test_session_extraction()
