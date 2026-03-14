"""Proof of concept for playwright-stealth on account.amd.com."""

import time
import os
from playwright.sync_api import sync_playwright
import playwright_stealth

def test_pw_stealth():
    print("Starting playwright-stealth PoC...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-http2"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Apply stealth by looking for the function in the module
        try:
            # It's likely in playwright_stealth.stealth.stealth or similar
            # based on typical Python package structures where the module 
            # and function share a name.
            from playwright_stealth.stealth import stealth as stealth_func
            stealth_func(page)
            print("Applied stealth to page via playwright_stealth.stealth.stealth")
        except Exception as e:
            print(f"Failed to apply stealth from playwright_stealth.stealth: {e}")
            try:
                # Try from the top level if it was imported there
                playwright_stealth.stealth(page)
                print("Applied stealth to page via playwright_stealth.stealth (top level)")
            except Exception as e2:
                print(f"Failed second stealth attempt: {e2}")

        try:
            url = "https://account.amd.com/"
            print(f"Navigating to {url}...")
            
            # Navigate and wait for some time to settle
            page.goto(url, wait_until="commit", timeout=60000)
            time.sleep(15) # Wait for redirects and JS
            
            print(f"Current URL: {page.url}")
            print(f"Page Title: {page.title()}")
            
            # Take a screenshot
            page.screenshot(path="pw-stealth-initial.png")
            print("Initial screenshot saved to pw-stealth-initial.png")
            
            # Wait for potential redirects and elements
            print("Waiting for login elements...")
            
            # Common selectors for AMD/Microsoft login
            selectors = [
                "input[name='loginfmt']",
                "#i0116",
                "input[type='email']"
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
            
            if not found:
                print("Could not find standard login elements. Page body text snippet:")
                try:
                    body_text = page.locator("body").inner_text()
                    print(body_text[:500] + "...")
                except:
                    print("Could not even get body text.")
            else:
                print("Successfully verified access to login page with playwright-stealth!")
                
            page.screenshot(path="pw-stealth-final.png")
            print("Final screenshot saved to pw-stealth-final.png")
            
        except Exception as exc:
            print(f"Navigation error: {exc}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_pw_stealth()
