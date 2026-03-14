"""Proof of concept for standard Selenium on account.amd.com."""

import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_selenium_amd():
    print("Starting Selenium PoC...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Add a real user-agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
    
    # Point to Playwright-managed Chromium if it exists
    pw_chrome = "/home/tcollins/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome"
    if os.path.exists(pw_chrome):
        print(f"Using Chromium from Playwright: {pw_chrome}")
        chrome_options.binary_location = pw_chrome
    
    # webdriver-manager will handle the matching of driver to chrome version
    print("Installing/Resolving ChromeDriver...")
    service = Service(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        url = "https://account.amd.com/"
        print(f"Navigating to {url}...")
        driver.get(url)
        
        # Give some time for JS to settle
        time.sleep(10)
        
        print(f"Current URL: {driver.current_url}")
        print(f"Page Title: {driver.title}")
        
        # Capture screenshot
        driver.save_screenshot("selenium-poc-initial.png")
        print("Initial screenshot saved to selenium-poc-initial.png")
        
        # Check for login elements
        print("Waiting for login elements...")
        wait = WebDriverWait(driver, 30)
        
        selectors = [
            (By.NAME, "loginfmt"),
            (By.ID, "i0116"),
            (By.CSS_SELECTOR, "input[type='email']")
        ]
        
        found = False
        for by, selector in selectors:
            try:
                element = wait.until(EC.visibility_of_element_located((by, selector)))
                print(f"Found login element with {by}={selector}")
                found = True
                break
            except:
                continue
        
        if not found:
            print("Could not find standard login elements. Page title snippet:")
            print(f"URL: {driver.current_url}")
            print(f"Title: {driver.title}")
            # Try to print some body text if elements fail
            try:
                body = driver.find_element(By.TAG_NAME, "body").text
                print(f"Body text snippet: {body[:500]}...")
            except:
                pass
        else:
            print("Successfully verified access to login page with Selenium!")
            
        driver.save_screenshot("selenium-poc-final.png")
        print("Final screenshot saved to selenium-poc-final.png")
        
    except Exception as exc:
        print(f"Selenium error: {exc}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_selenium_amd()
