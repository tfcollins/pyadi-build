"""Test initial access to account.amd.com."""

import time
import pytest
from adibuild.core.vivado import PlaywrightDownloadStrategy

@pytest.mark.integration
@pytest.mark.slow
def test_amd_account_access():
    """Verify that account.amd.com is reachable and loads expected login elements.
    
    This test includes delays to avoid DDOS/blocking as requested.
    It does not require credentials as it only checks the initial landing page.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("playwright not installed; skip AMD account access test")

    strategy = PlaywrightDownloadStrategy()
    
    with sync_playwright() as p:
        # Use existing launch options for consistency (headless, no-sandbox if root, etc.)
        browser = p.chromium.launch(**strategy._launch_options())
        
        # We use a real user-agent to reduce the chance of being flagged as a bot
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        
        # Use a real release for the URL
        from adibuild.core.vivado import SUPPORTED_RELEASES
        release = SUPPORTED_RELEASES["2023.2"]
        target_url = strategy._auth_bootstrap_url(release)
        
        try:
            # Initial delay before access to avoid rapid-fire requests
            time.sleep(5)
            
            # Navigate to the page with a generous timeout
            print(f"Navigating to {target_url}...")
            page.goto(target_url, wait_until="commit", timeout=180000)
            
            # Delay after page load to mimic human behavior and allow dynamic content to load
            time.sleep(10)
            
            # Check for common login elements (email field)
            # We use selectors defined in the production PlaywrightDownloadStrategy
            found_login_element = False
            
            # We look for email fields or general login markers in the URL
            for selector in strategy.EMAIL_SELECTORS:
                if page.locator(selector).is_visible():
                    found_login_element = True
                    break
            
            # If not found immediately, it might be a redirect (e.g. to Microsoft/Okta login)
            if not found_login_element:
                # Wait a bit more for potential redirects to settle
                time.sleep(5)
                for selector in strategy.EMAIL_SELECTORS:
                    if page.locator(selector).is_visible():
                        found_login_element = True
                        break
            
            # Check for other markers if selectors don't match exactly (SSO providers often change them)
            current_url = page.url.lower()
            if not found_login_element:
                login_markers = ["login", "signin", "oauth", "saml", "microsoft", "okta"]
                if any(marker in current_url for marker in login_markers):
                    found_login_element = True
            
            # Assert that we reached some form of login or authentication gate
            assert found_login_element, (
                f"Could not verify login access on {page.url}. "
                "The page might have changed its structure or blocked the request."
            )
                
        finally:
            # Final delay before closing the browser
            time.sleep(2)
            browser.close()
