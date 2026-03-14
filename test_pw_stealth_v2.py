"""Verification script using playwright-stealth for account.amd.com."""

import time
import os
from playwright.sync_api import sync_playwright
import playwright_stealth

def test_pw_stealth():
    print("Starting playwright-stealth PoC...")
    
    with sync_playwright() as p:
        # Launch WITHOUT headless so it works with xvfb
        browser = p.chromium.launch(headless=False, args=["--disable-http2"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        
        # Apply stealth
        try:
            from playwright_stealth import Stealth
            Stealth().apply_stealth_sync(page)
            print("Applied stealth to page via Stealth().apply_stealth_sync")
        except Exception as e:
            print(f"Failed to apply stealth: {e}")

        try:
            url = "https://account.amd.com/"
            print(f"Navigating to {url}...")
            
            # Navigate
            page.goto(url, wait_until="commit", timeout=120000)
            time.sleep(15) # Wait for redirects
            
            print(f"Current URL: {page.url}")
            print(f"Page Title: {page.title()}")
            
            page.screenshot(path="pw-poc-initial.png")
            print("Initial screenshot saved to pw-poc-initial.png")
            
            print("Waiting for login elements...")
            
            # Okta/AMD selectors
            selectors = [
                "input[name='loginfmt']",
                "#i0116",
                "input[type='email']",
                "input[name='identifier']",
                "#okta-signin-username"
            ]
            
            found = False
            for selector in selectors:
                try:
                    page.wait_for_selector(selector, state="visible", timeout=10000)
                    print(f"Found login element with selector: {selector}")
                    found = True
                    break
                except:
                    continue
            
            if found:
                print("Successfully verified access to login page with playwright-stealth!")
            else:
                print("Could not find standard login elements.")
                try:
                    body_text = page.locator("body").inner_text()
                    print(f"Body text: {body_text[:500]}...")
                except:
                    pass
                
            page.screenshot(path="pw-poc-final.png")
            print("Final screenshot saved to pw-poc-final.png")
            
        except Exception as exc:
            print(f"Navigation error: {exc}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_pw_stealth()
