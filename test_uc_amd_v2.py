"""Verification script using undetected-chromedriver for account.amd.com."""

import time
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_uc_amd():
    print("Starting undetected-chromedriver PoC...")
    
    options = uc.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-http2")
    
    # Point to Playwright-managed Chromium if it exists
    pw_chrome = "/home/tcollins/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome"
    if os.path.exists(pw_chrome):
        print(f"Using Chromium from Playwright: {pw_chrome}")
        options.binary_location = pw_chrome
    
    # undetected-chromedriver handles driver matching and patching
    try:
        driver = uc.Chrome(options=options, version_main=145)
        
        url = "https://account.amd.com/"
        print(f"Navigating to {url}...")
        driver.get(url)
        
        # Give some time for JS and redirects
        time.sleep(15)
        
        print(f"Current URL: {driver.current_url}")
        print(f"Page Title: {driver.title}")
        
        driver.save_screenshot("uc-poc-initial.png")
        print("Initial screenshot saved to uc-poc-initial.png")
        
        print("Waiting for login elements...")
        wait = WebDriverWait(driver, 45)
        
        selectors = [
            (By.NAME, "loginfmt"),
            (By.ID, "i0116"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.NAME, "identifier"),
            (By.ID, "okta-signin-username"),
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
        
        if found:
            print("Successfully verified access to login page with undetected-chromedriver!")
        else:
            print("Could not find standard login elements.")
            try:
                print(f"Body text: {driver.find_element(By.TAG_NAME, 'body').text[:1000]}...")
            except:
                pass
            
        driver.save_screenshot("uc-poc-final.png")
        print("Final screenshot saved to uc-poc-final.png")
        
    except Exception as exc:
        print(f"UC error: {exc}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    test_uc_amd()
