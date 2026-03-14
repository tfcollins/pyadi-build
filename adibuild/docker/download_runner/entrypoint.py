"""Entrypoint script for the Vivado download runner container."""

import json
import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

def main():
    username = os.environ.get("AMD_USERNAME")
    password = os.environ.get("AMD_PASSWORD")
    filename = os.environ.get("VIVADO_FILENAME")
    download_url = os.environ.get("VIVADO_DOWNLOAD_URL")
    
    if not all([username, password, filename, download_url]):
        print("Missing required environment variables: AMD_USERNAME, AMD_PASSWORD, VIVADO_FILENAME, VIVADO_DOWNLOAD_URL")
        sys.exit(1)

    print(f"Starting Vivado download for {filename}...")
    
    with sync_playwright() as p:
        # Launch WITHOUT headless so it works with xvfb
        browser = p.chromium.launch(headless=False, args=["--disable-http2"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            accept_downloads=True
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)

        try:
            # Step 1: Navigate to the targeted AMD download form URL
            auth_url = f"https://account.amd.com/en/forms/downloads/xef.html?filename={filename}"
            print(f"Navigating to {auth_url}...")
            page.goto(auth_url, wait_until="commit", timeout=120000)
            time.sleep(10)
            
            # Step 2: Perform Login
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
            
            # Step 3: Fill Download Form if needed
            # (AMD often requires an export control form)
            print("Checking for AMD export control form...")
            # This is a simplified version of the logic in vivado.py
            try:
                # Common fields in the form
                form_fields = {
                    "First_Name": "Travis",
                    "Last_Name": "Collins",
                    "Company": "Analog Devices Inc",
                    "Address_1": "804 Woburn Street",
                    "City": "Wilmington",
                    "Zip_Code": "01887",
                    "Email": username,
                    "Phone": "9786585555",
                }
                
                for selector, value in form_fields.items():
                    try:
                        loc = page.locator(f"[name='{selector}'], #{selector}").first
                        if loc.is_visible():
                            loc.fill(value)
                    except:
                        pass
                
                # Check checkboxes
                checkboxes = page.locator("input[type='checkbox']").all()
                for cb in checkboxes:
                    if not cb.is_checked():
                        cb.click()
                
                # Click download/submit
                submit = page.locator("input[type='submit'], button[type='submit'], #submit, input[value='Download']").first
                if submit.is_visible():
                    print("Submitting download form...")
                    with page.expect_download(timeout=120000) as download_info:
                        submit.click()
                    download = download_info.value
                    print(f"Download started: {download.suggested_filename}")
                    
                    # Save to /downloads
                    dest_path = Path("/downloads") / filename
                    download.save_as(str(dest_path))
                    print(f"Successfully downloaded to {dest_path}")
                    return
            except Exception as e:
                print(f"Form submission failed or not needed: {e}")

            # Step 4: Last resort - direct navigation to download URL
            print(f"Trying direct navigation to download URL: {download_url}")
            with page.expect_download(timeout=120000) as download_info:
                page.goto(download_url, wait_until="commit")
            download = download_info.value
            dest_path = Path("/downloads") / filename
            download.save_as(str(dest_path))
            print(f"Successfully downloaded via direct navigation to {dest_path}")
                
        except Exception as exc:
            print(f"Error during download: {exc}")
            page.screenshot(path="/downloads/error.png")
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    main()
