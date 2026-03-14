"""Vivado download and installation helpers."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests

try:
    from selenium.webdriver.common.by import By
except ImportError:
    By = None

from typing import Any, Protocol, runtime_checkable

from adibuild.core.toolchain import ToolchainError, ToolchainInfo
from adibuild.utils.logger import get_logger


@runtime_checkable
class VivadoDownloadStrategy(Protocol):
    """Common interface for Vivado installer download methods."""

    def download(
        self,
        release: VivadoRelease,
        destination: Path,
        credentials: VivadoCredentials | None = None,
    ) -> Path:
        """Download the requested Vivado release to the destination path."""
        ...


@dataclass(frozen=True)
class VivadoRelease:
    """Official AMD Vivado Linux installer metadata."""

    version: str
    installer_version: str
    install_version: str
    filename: str
    download_url: str
    digests_url: str | None
    edition: str = "Vivado ML Standard"


@dataclass(frozen=True)
class VivadoCredentials:
    """Credentials used for AMD account authentication."""

    username: str
    password: str

    @classmethod
    def from_env(cls) -> VivadoCredentials | None:
        """Load credentials from environment variables."""
        username = os.environ.get("AMD_USERNAME")
        password = os.environ.get("AMD_PASSWORD")
        if not username or not password:
            return None
        return cls(username=username, password=password)


@dataclass(frozen=True)
class VivadoInstallRequest:
    """Input for a Vivado installation run."""

    version: str
    install_dir: Path = Path("/opt/Xilinx")
    cache_dir: Path | None = None
    extract_dir: Path | None = None
    installer_path: Path | None = None
    config_path: Path | None = None
    edition: str | None = None
    agree_webtalk_terms: bool = True
    credentials: VivadoCredentials | None = None


@dataclass(frozen=True)
class VivadoInstallResult:
    """Result of a Vivado install workflow."""

    release: VivadoRelease
    installer_path: Path
    extract_dir: Path
    toolchain: ToolchainInfo


class VivadoDownloadError(ToolchainError):
    """Raised when the installer binary cannot be downloaded."""


class VivadoAuthRequiredError(VivadoDownloadError):
    """Raised when AMD authentication is required for download."""


class VivadoInstallError(ToolchainError):
    """Raised when the installer client fails."""


SUPPORTED_RELEASES = {
    "2023.2": VivadoRelease(
        version="2023.2",
        installer_version="2023.2",
        install_version="2023.2",
        filename="FPGAs_AdaptiveSoCs_Unified_2023.2_1013_2256_Lin64.bin",
        download_url=(
            "https://account.amd.com/en/forms/downloads/xef.html"
            "?filename=FPGAs_AdaptiveSoCs_Unified_2023.2_1013_2256_Lin64.bin"
        ),
        digests_url=(
            "https://www.xilinx.com/content/dam/xilinx/support/download/2023-2/"
            "vivado/FPGAs_AdaptiveSoCs_Unified_2023.2_1013_2256_Lin64.bin.digests"
        ),
    ),
    "2025.1": VivadoRelease(
        version="2025.1",
        installer_version="2025.1.1",
        install_version="2025.1",
        filename="FPGAs_AdaptiveSoCs_Unified_SDI_2025.1.1_0912_0129_Lin64.bin",
        download_url=(
            "https://account.amd.com/en/forms/downloads/xef.html"
            "?filename=FPGAs_AdaptiveSoCs_Unified_SDI_2025.1.1_0912_0129_Lin64.bin"
        ),
        digests_url=(
            "https://download.amd.com/opendownload/installer/2025.1.1_0912_2/"
            "FPGAs_AdaptiveSoCs_Unified_SDI_2025.1.1_0912_0129_Lin64.bin.digests"
        ),
    ),
    "2025.1.1": VivadoRelease(
        version="2025.1",
        installer_version="2025.1.1",
        install_version="2025.1",
        filename="FPGAs_AdaptiveSoCs_Unified_SDI_2025.1.1_0912_0129_Lin64.bin",
        download_url=(
            "https://account.amd.com/en/forms/downloads/xef.html"
            "?filename=FPGAs_AdaptiveSoCs_Unified_SDI_2025.1.1_0912_0129_Lin64.bin"
        ),
        digests_url=(
            "https://download.amd.com/opendownload/installer/2025.1.1_0912_2/"
            "FPGAs_AdaptiveSoCs_Unified_SDI_2025.1.1_0912_0129_Lin64.bin.digests"
        ),
    ),
}

DEFAULT_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
}


class SessionDownloadStrategy:
    """Download Vivado by extracting a browser session to a Requests session."""

    def __init__(self):
        self.logger = get_logger("adibuild.vivado.session")

    def download(
        self,
        release: VivadoRelease,
        destination: Path,
        credentials: VivadoCredentials | None = None,
    ) -> Path:
        """Log in via browser, extract cookies, and download via Requests."""
        if not credentials:
            raise VivadoAuthRequiredError(
                "Session download strategy requires AMD credentials"
            )

        # 1. Login and extract session using Playwright (most reliable for login)
        self.logger.info("Extracting authenticated AMD session via Playwright")
        pw_strategy = PlaywrightDownloadStrategy()
        
        # We need a way to get the session without performing the full download
        # I'll add a helper method to PlaywrightDownloadStrategy or just use it here
        # For now, I'll use a simplified extraction logic here or refactor PlaywrightDownloadStrategy
        
        # Refactoring PlaywrightDownloadStrategy to expose session extraction would be better.
        # But for this task, I'll implement a standalone extraction.
        
        with pw_strategy._sync_playwright() as playwright:
            browser = playwright.chromium.launch(**pw_strategy._launch_options())
            context = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            )
            page = context.new_page()
            
            try:
                from playwright_stealth import Stealth
                Stealth().apply_stealth_sync(page)
            except ImportError:
                pass

            auth_url = pw_strategy._auth_bootstrap_url(release)
            pw_strategy._goto_with_retry(
                page, auth_url, "session-extraction-login", credentials=credentials
            )
            pw_strategy._login_if_needed(page, credentials)
            
            # Extract session
            session = pw_strategy._session_from_browser_context(context, page)
            browser.close()

        # 2. Use Requests strategy with the extracted session
        self.logger.info("Session extracted; starting direct download via Requests")
        req_strategy = RequestsDownloadStrategy(session=session)
        return req_strategy.download(release, destination, bootstrap=False)


class DockerDownloadStrategy:
    """Download Vivado using a specialized ephemeral Docker container."""

    def __init__(self):
        self.logger = get_logger("adibuild.vivado.docker")

    def download(
        self,
        release: VivadoRelease,
        destination: Path,
        credentials: VivadoCredentials | None = None,
    ) -> Path:
        """Run the download in a Docker container."""
        if not credentials:
            raise VivadoAuthRequiredError(
                "Docker download strategy requires AMD credentials"
            )

        from adibuild.core.docker import DockerDownloadRunner

        runner = DockerDownloadRunner()
        return runner.download(
            version=release.version,
            destination=destination,
            credentials=credentials,
        )


class RequestsDownloadStrategy:
    """Best-effort direct download via HTTP session."""

    def __init__(
        self,
        session: requests.Session | None = None,
        max_attempts: int = 3,
        backoff_seconds: int = 10,
    ):
        self.session = session or requests.Session()
        self.max_attempts = max_attempts
        self.backoff_seconds = backoff_seconds
        self.logger = get_logger("adibuild.vivado.http")
        self._apply_browser_headers()

    def download(
        self,
        release: VivadoRelease,
        destination: Path,
        bootstrap: bool = True,
    ) -> Path:
        """Download the installer or fail if the endpoint requires login."""
        last_error: tuple[str, str, Exception] | None = None
        for attempt in range(1, self.max_attempts + 1):
            self.logger.info(
                "Starting direct AMD download request "
                f"(attempt {attempt}/{self.max_attempts}) to {release.download_url}"
            )
            try:
                return self._download_once(release, destination, bootstrap=bootstrap)
            except _RetryableDownloadError as exc:
                last_error = (exc.stage, exc.message, exc.original_exc)
                if destination.exists():
                    destination.unlink(missing_ok=True)

                if attempt == self.max_attempts:
                    raise VivadoDownloadError(
                        f"Vivado download failed at stage={exc.stage} after "
                        f"{self.max_attempts} attempts: {exc.message}"
                    ) from exc.original_exc

                delay = self.backoff_seconds * attempt
                self.logger.warning(
                    "Direct AMD download attempt "
                    f"{attempt}/{self.max_attempts} failed at stage={exc.stage}: "
                    f"{exc.message}. Retrying in {delay}s"
                )
                time.sleep(delay)

        stage, message, original_exc = last_error or (
            "unknown",
            "download failed",
            RuntimeError("download failed"),
        )
        raise VivadoDownloadError(
            f"Vivado download failed at stage={stage}: {message}"
        ) from original_exc

    def _download_once(
        self,
        release: VivadoRelease,
        destination: Path,
        bootstrap: bool = True,
    ) -> Path:
        """Perform a single direct download attempt."""
        if bootstrap:
            self._bootstrap_amd_session(release)
        try:
            response = self.session.get(
                release.download_url,
                stream=True,
                allow_redirects=True,
                timeout=120,
            )
        except requests.Timeout as exc:
            raise _RetryableDownloadError(
                stage="initial-http-request",
                message=f"timed out while requesting {release.download_url}",
                original_exc=exc,
            ) from exc
        except requests.RequestException as exc:
            raise _RetryableDownloadError(
                stage="initial-http-request",
                message=f"request to {release.download_url} failed with {exc}",
                original_exc=exc,
            ) from exc

        final_url = response.url.lower()
        content_type = response.headers.get("content-type", "").lower()
        disposition = response.headers.get("content-disposition", "")
        content_length = response.headers.get("content-length", "unknown")
        self.logger.info(
            "AMD download response: "
            f"status={response.status_code}, final_url={response.url}, "
            f"content_type={content_type or 'unknown'}, content_length={content_length}"
        )

        if response.status_code >= 400:
            response.close()
            raise VivadoDownloadError(
                f"AMD download endpoint returned HTTP {response.status_code}"
            )

        is_binary = "application/octet-stream" in content_type or disposition
        looks_like_login = any(
            marker in final_url
            for marker in ("login", "signin", "account.amd.com", "oauth", "saml")
        )
        if looks_like_login and not is_binary:
            response.close()
            raise VivadoAuthRequiredError(
                "AMD requires an authenticated download session for this installer"
            )
        if not is_binary:
            response.close()
            raise VivadoDownloadError(
                f"Unexpected non-binary response from AMD download endpoint: {final_url}"
            )

        destination.parent.mkdir(parents=True, exist_ok=True)
        downloaded_bytes = 0
        progress_interval = 100 * 1024 * 1024
        next_progress_log = progress_interval
        try:
            with destination.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
                        downloaded_bytes += len(chunk)
                        if downloaded_bytes >= next_progress_log:
                            self.logger.info(
                                "Direct AMD download progress: "
                                f"{downloaded_bytes / (1024 * 1024):.1f} MiB written "
                                f"to {destination}"
                            )
                            next_progress_log += progress_interval
        except requests.Timeout as exc:
            response.close()
            raise _RetryableDownloadError(
                stage="download-stream",
                message=(
                    f"timed out while streaming {response.url} after "
                    f"{downloaded_bytes / (1024 * 1024):.1f} MiB"
                ),
                original_exc=exc,
            ) from exc
        except requests.RequestException as exc:
            response.close()
            raise _RetryableDownloadError(
                stage="download-stream",
                message=(
                    f"streaming {response.url} failed after "
                    f"{downloaded_bytes / (1024 * 1024):.1f} MiB with {exc}"
                ),
                original_exc=exc,
            ) from exc
        response.close()
        self.logger.info(
            "Completed direct AMD download: "
            f"{downloaded_bytes / (1024 * 1024):.1f} MiB saved to {destination}"
        )
        return destination

    def _apply_browser_headers(self) -> None:
        """Apply browser-like defaults so AMD does not treat requests as a bare bot."""
        for key, value in DEFAULT_BROWSER_HEADERS.items():
            current = self.session.headers.get(key)
            if (
                key == "User-Agent"
                and current
                and not current.startswith("python-requests/")
            ):
                continue
            self.session.headers[key] = value

    def _bootstrap_amd_session(self, release: VivadoRelease) -> None:
        """Prime AMD/F5 session cookies before hitting auth-gated download URLs."""
        parsed = urlparse(release.download_url)
        if parsed.netloc.lower() != "account.amd.com":
            return

        bootstrap_url = f"{parsed.scheme}://{parsed.netloc}/"
        self.logger.info(f"Bootstrapping AMD auth gateway at {bootstrap_url}")
        try:
            response = self.session.get(
                bootstrap_url,
                allow_redirects=False,
                timeout=120,
            )
        except requests.RequestException as exc:
            self.logger.warning(
                f"AMD auth gateway bootstrap failed for {bootstrap_url}: {exc}"
            )
            return

        location = response.headers.get("location")
        self.logger.info(
            "AMD auth gateway bootstrap response: "
            f"status={response.status_code}, location={location or 'none'}"
        )
        response.close()


@dataclass(frozen=True)
class _RetryableDownloadError(Exception):
    """Internal exception for retryable AMD download failures."""

    stage: str
    message: str
    original_exc: Exception


class SeleniumDownloadStrategy:
    """Fallback browser-driven download via Selenium."""

    EMAIL_SELECTORS = (
        ("name", "loginfmt"),
        ("name", "identifier"),
        ("id", "i0116"),
        ("css selector", "input[type='email']"),
        ("name", "email"),
    )
    PASSWORD_SELECTORS = (
        ("name", "password"),
        ("name", "credentials.passcode"),
        ("id", "i0118"),
        ("css selector", "input[type='password']"),
    )
    SUBMIT_SELECTORS = (
        ("id", "idSIButton9"),
        ("css selector", "input[type='submit']"),
        ("css selector", "button[type='submit']"),
        ("css selector", "input[value='Sign In']"),
        ("css selector", "input[value='Sign in']"),
    )

    def __init__(self, screenshot_dir: Path | None = None):
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.support.ui import WebDriverWait
        except ImportError as exc:
            raise VivadoDownloadError(
                "Selenium download fallback requires the 'vivado-selenium' extra"
            ) from exc

        self._webdriver = webdriver
        self._chrome_options = Options
        self._chrome_service = Service
        self._by = By
        self._ec = EC
        self._wait = WebDriverWait
        self.logger = get_logger("adibuild.vivado.selenium")
        
        # Priority: constructor arg > env var > default home dir
        self.screenshot_dir = (
            screenshot_dir 
            or Path(os.environ.get("ADIBUILD_VIVADO_DEBUG_DIR", ""))
            if os.environ.get("ADIBUILD_VIVADO_DEBUG_DIR")
            else Path.home() / ".adibuild" / "toolchains" / "vivado" / "debug"
        )

    def _take_screenshot(self, driver, name: str) -> None:
        """Capture a browser screenshot for debugging."""
        try:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            path = self.screenshot_dir / f"{timestamp}-{name}.png"
            driver.save_screenshot(str(path))
            self.logger.info(f"Captured debug screenshot: {path}")
        except Exception as exc:
            self.logger.warning(f"Failed to capture debug screenshot '{name}': {exc}")

    def download(
        self,
        release: VivadoRelease,
        destination: Path,
        credentials: VivadoCredentials,
    ) -> Path:
        """Login to AMD and download the installer using Selenium."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.logger.info(
            f"Starting Selenium-authenticated AMD download for {release.filename}"
        )

        options = self._chrome_options()
        headless = os.environ.get("ADIBUILD_BROWSER_HEADLESS", "1").lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        )

        # Selenium 4.6+ handles driver management automatically
        driver = self._webdriver.Chrome(options=options)
        
        # Apply selenium-stealth if available
        try:
            from selenium_stealth import stealth
            stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Linux x86_64",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            self.logger.info("Applied selenium-stealth to the driver")
        except ImportError:
            pass

        # Set download behavior for headless mode
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": str(destination.parent)
        })

        try:
            # Using the actual bootstrap URL is more reliable for triggering the right login flow
            auth_url = f"https://account.amd.com/en/forms/downloads/xef.html?filename={release.filename}"
            self.logger.info(f"Opening AMD bootstrap page {auth_url}")
            driver.get(auth_url)
            
            self._login_if_needed(driver, credentials)
            
            # Form should be on the current page after login
            self._fill_form_if_needed(driver)
            
            self.logger.info("Waiting for installer download to complete")
            # For Selenium, we might need to wait for the file to appear in destination.parent
            # or just wait a reasonable time if we can't detect it easily.
            try:
                # Give it up to 10 minutes to start the download
                self._wait_for_download(driver, destination.parent, release.filename, timeout=600)
                
                # Check for completion (up to 3 hours for 10-20GB installer)
                self.logger.info("Waiting for installer download to complete (this may take a long time)")
                self._wait_for_download_completion(driver, destination.parent, release.filename, timeout=10800)
                
                target = destination
                # Check if it was saved with a different name
                if not target.exists():
                    candidates = list(destination.parent.glob(f"*{release.filename}*"))
                    if candidates:
                        target = candidates[0]
                self.logger.info(f"Selenium download complete: {target}")
                return target
            except VivadoDownloadError as e:
                self.logger.warning(f"Browser download failed or timed out: {e}")
                self.logger.info("Trying direct download with cookies as fallback")
                session = self._session_from_webdriver(driver)
                return RequestsDownloadStrategy(session=session).download(release, destination)

        finally:
            driver.quit()

    def _session_from_webdriver(self, driver) -> requests.Session:
        """Build a requests session from authenticated browser cookies."""
        session = requests.Session()
        for cookie in driver.get_cookies():
            session.cookies.set(
                cookie["name"],
                cookie["value"],
                domain=cookie.get("domain"),
                path=cookie.get("path", "/"),
            )
        user_agent = driver.execute_script("return navigator.userAgent;")
        if user_agent:
            session.headers.update({"User-Agent": user_agent})
        return session

    def _login_if_needed(self, driver, credentials: VivadoCredentials) -> None:
        wait = self._wait(driver, 45)
        from selenium.webdriver.common.keys import Keys
        try:
            # Username and Password
            self._take_screenshot(driver, "selenium-login-start")
            
            self.logger.info(f"Filling and submitting login form for {credentials.username}")
            driver.execute_script(f"""
                const user = "{credentials.username}";
                const pass = "{credentials.password}";
                const userEl = document.getElementsByName('identifier')[0] || document.querySelector('input[type="email"]');
                const passEl = document.getElementsByName('credentials.passcode')[0] || document.querySelector('input[type="password"]');
                const btn = document.querySelector('input[type="submit"], button[type="submit"], #submit');
                
                if (userEl) {{
                    userEl.value = user;
                    userEl.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    userEl.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
                if (passEl) {{
                    passEl.value = pass;
                    passEl.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    passEl.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
                if (btn) {{
                    btn.click();
                }}
            """)
            time.sleep(10)
            
            # Stay signed in?
            try:
                stay_signed_in = wait.until(self._ec.element_to_be_clickable((self._by.ID, "idSIButton9")))
                stay_signed_in.click()
                time.sleep(2)
            except:
                pass
                
        except Exception as e:
            self.logger.warning(f"Login failed or not needed: {e}")
            self._take_screenshot(driver, "selenium-login-error")
                
            # Stay signed in?
            try:
                stay_signed_in = wait.until(self._ec.element_to_be_clickable((self._by.ID, "idSIButton9")))
                stay_signed_in.click()
                time.sleep(2)
            except:
                pass

    def _fill_form_if_needed(self, driver) -> None:
        self.logger.info("Checking for AMD export control form")
        time.sleep(5)
        
        # Dismiss cookie banner if present
        try:
            banner_btn = driver.find_element(self._by.ID, "onetrust-accept-btn-handler")
            if banner_btn.is_displayed():
                self.logger.info("Dismissing cookie banner")
                banner_btn.click()
                time.sleep(2)
        except:
            pass

        self._take_screenshot(driver, "selenium-before-form")
        
        # Aggressive form filling
        form_fields = {
            "First_Name": "Travis",
            "Last_Name": "Collins",
            "Company": "Analog Devices Inc",
            "Address_1": "804 Woburn Street",
            "Address_2": "N/A",
            "City": "Wilmington",
            "Zip_Code": "01887",
            "Job_Function": "Other",
            "Country": "United States",
            "State": "Massachusetts",
            "Email": "travis.collins@analog.com",
            "Phone": "9786585555",
        }
        
        try:
            # 1. Fill in main frame using send_keys where possible
            from selenium.webdriver.support.ui import Select
            
            # Special handling for Country and State as they often have dependent logic
            try:
                country_el = driver.find_element(self._by.NAME, "Country")
                s = Select(country_el)
                try: s.select_by_value("US")
                except: s.select_by_visible_text("United States")
                time.sleep(1)
            except: pass
            
            try:
                state_el = driver.find_element(self._by.NAME, "State")
                s = Select(state_el)
                try: s.select_by_value("MA")
                except: s.select_by_visible_text("Massachusetts")
                time.sleep(1)
            except: pass

            for name, value in form_fields.items():
                try:
                    # Try finding by name or id
                    el = None
                    for selector in [f"[name='{name}']", f"#{name}", f"[id*='{name}']"]:
                        try:
                            found = driver.find_elements(self._by.CSS_SELECTOR, selector)
                            for f in found:
                                if f.is_displayed():
                                    el = f
                                    break
                            if el: break
                        except: continue
                    
                    if el:
                        if el.tag_name == "select":
                            from selenium.webdriver.support.ui import Select
                            s = Select(el)
                            try:
                                s.select_by_visible_text(value)
                            except:
                                try:
                                    s.select_by_value(value)
                                except:
                                    if len(s.options) > 1: s.select_by_index(1)
                        else:
                            el.clear()
                            el.send_keys(value)
                except Exception as e:
                    self.logger.debug(f"Could not fill field {name}: {e}")

            # 2. Also try aggressive JS fill as fallback/reinforcement
            self._fill_frame(driver, form_fields)
            
            # 3. Check and fill in all iframes
            iframes = driver.find_elements(self._by.TAG_NAME, "iframe")
            self.logger.info(f"Found {len(iframes)} iframes on page")
            for i, iframe in enumerate(iframes):
                try:
                    driver.switch_to.frame(iframe)
                    self.logger.info(f"Checking iframe {i} for form fields")
                    if self._fill_frame(driver, form_fields):
                        self.logger.info(f"Filled form in iframe {i}")
                    driver.switch_to.default_content()
                except Exception as e:
                    self.logger.debug(f"Could not switch to iframe {i}: {e}")
                    driver.switch_to.default_content()

            # Attempt submission from wherever the form was found
            self._take_screenshot(driver, "selenium-form-filled")
            
            # Log what we filled
            try:
                inputs = driver.execute_script("""
                    return Array.from(document.querySelectorAll('input, select')).map(el => ({
                        name: el.name || el.id,
                        type: el.tagName,
                        value: el.value,
                        visible: el.offsetWidth > 0 && el.offsetHeight > 0
                    })).filter(i => i.visible);
                """)
                self.logger.info(f"Visible form fields after filling: {inputs}")
            except:
                pass

            self._submit_form(driver)
            time.sleep(10)
            
            self.logger.info(f"Page state after submission: URL={driver.current_url} Title='{driver.title}'")
            
            # Check for new windows
            if len(driver.window_handles) > 1:
                self.logger.info(f"Found {len(driver.window_handles)} windows/tabs")
                driver.switch_to.window(driver.window_handles[-1])
                self.logger.info(f"Switched to window: {driver.current_url}")
                self._take_screenshot(driver, "selenium-new-window")
                
            # Check for errors after submission
            try:
                errors = driver.find_elements(self._by.CSS_SELECTOR, ".error, .errormsg, .alert-danger, [id*='error']")
                if errors:
                    err_texts = [e.text for e in errors if e.is_displayed()]
                    if err_texts:
                        self.logger.warning(f"Detected potential form errors after submission: {err_texts}")
            except:
                pass

            self._take_screenshot(driver, "selenium-after-form-submit")
        except Exception as e:
            self.logger.warning(f"Failed to fill form: {e}")

    def _fill_frame(self, driver, fields) -> bool:
        """Fill form fields in current frame via JS."""
        return driver.execute_script(f"""
            const fields = {json.dumps(fields)};
            let filled = false;
            for (const [name, value] of Object.entries(fields)) {{
                const elements = document.querySelectorAll(`[name="${{name}}"], [id="${{name}}"]`);
                elements.forEach(el => {{
                    if (el.tagName === 'SELECT') {{
                        const option = Array.from(el.options).find(opt => 
                            opt.text.toLowerCase().includes(value.toLowerCase()) || 
                            opt.value.toLowerCase().includes(value.toLowerCase())
                        );
                        if (option) el.value = option.value;
                        else if (el.options.length > 1) el.selectedIndex = 1;
                    }} else {{
                        el.value = value;
                    }}
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    filled = true;
                }});
            }}
            
            // Also click all checkboxes
            const checkboxes = document.querySelectorAll('input[type="checkbox"]');
            checkboxes.forEach(cb => {{
                if (!cb.checked) {{
                    cb.click();
                    filled = true;
                }}
            }});
            
            return filled;
        """)

    def _submit_form(self, driver) -> None:
        """Attempt to submit the form in the current frame or all frames."""
        submit_selectors = (
            ("css selector", "input[type='submit']"),
            ("css selector", "button[type='submit']"),
            ("id", "submit"),
            ("css selector", "input[value='Download']"),
            ("xpath", "//button[contains(text(), 'Download')]"),
            ("xpath", "//input[contains(@value, 'Download')]"),
        )
        
        def try_submit(d):
            # Try finding the element and clicking it natively
            for by, selector in submit_selectors:
                try:
                    btn = d.find_element(by, selector)
                    if btn.is_displayed() and btn.is_enabled():
                        self.logger.info(f"Clicking submit button: {selector}")
                        btn.click()
                        return True
                except:
                    continue
            
            # Fallback to JS click
            try:
                d.execute_script("""
                    const submit = document.querySelector('input[type="submit"], button[type="submit"], #submit, input[value="Download"]');
                    if (submit) {
                        submit.click();
                        return true;
                    }
                    const form = document.forms[0];
                    if (form) {
                        form.submit();
                        return true;
                    }
                    return false;
                """)
                return True
            except:
                return False

        self.logger.info("Attempting form submission in main frame")
        if try_submit(driver):
            self.logger.info("Form submission triggered in main frame")
            return

        # Also try in iframes
        iframes = driver.find_elements(self._by.TAG_NAME, "iframe")
        for i, iframe in enumerate(iframes):
            try:
                driver.switch_to.frame(iframe)
                self.logger.info(f"Attempting form submission in iframe {i}")
                if try_submit(driver):
                    self.logger.info(f"Form submission triggered in iframe {i}")
                    driver.switch_to.default_content()
                    return
                driver.switch_to.default_content()
            except:
                driver.switch_to.default_content()

    def _wait_for_download(self, driver, directory: Path, filename: str, timeout: int) -> None:
        """Wait for the download to START (file appears in directory)."""
        start_time = time.time()
        self.logger.info(f"Monitoring {directory} for {filename} to appear (timeout {timeout}s)")
        while time.time() - start_time < timeout:
            files = list(directory.iterdir())
            if files:
                for f in files:
                    if filename in f.name:
                        self.logger.info(f"Download started: {f.name}")
                        return
            time.sleep(5)
        raise VivadoDownloadError(f"Download did not start after {timeout}s")

    def _wait_for_download_completion(self, driver, directory: Path, filename: str, timeout: int) -> None:
        """Wait for the download to FINISH (no .crdownload or .tmp files)."""
        start_time = time.time()
        self.logger.info(f"Monitoring {directory} for {filename} to complete (timeout {timeout}s)")
        while time.time() - start_time < timeout:
            # Periodic screenshot during wait
            if int(time.time() - start_time) % 300 < 5:
                self._take_screenshot(driver, "selenium-download-waiting")
                
            files = list(directory.iterdir())
            downloading = False
            found = False
            for f in files:
                if filename in f.name:
                    if f.name.endswith(".crdownload") or f.name.endswith(".tmp"):
                        downloading = True
                    else:
                        found = True
            
            if found and not downloading:
                self.logger.info(f"Download completed for {filename}")
                return
            
            time.sleep(10)
        raise VivadoDownloadError(f"Download did not complete after {timeout}s")

    def _find_element(self, driver, selectors):
        for by, selector in selectors:
            try:
                element = driver.find_element(by, selector)
                if element.is_displayed():
                    return element
            except:
                continue
        return None

    def _click_element(self, driver, selectors):
        element = self._find_element(driver, selectors)
        if element:
            element.click()


class PlaywrightDownloadStrategy:
    """Optional browser-driven fallback for authenticated downloads."""

    EMAIL_SELECTORS = (
        "input[type='email']",
        "input[name='email']",
        "input[name='username']",
        "input[name='loginfmt']",
        "input[name='identifier']",
        "input[name='login']",
        "#i0116",
    )
    PASSWORD_SELECTORS = (
        "input[type='password']",
        "input[name='password']",
        "input[name='credentials.passcode']",
        "input[name='passwd']",
        "#i0118",
    )
    SUBMIT_SELECTORS = (
        "button[type='submit']",
        "input[type='submit']",
        "input[value='Sign In']",
        "input[value='Sign in']",
        "#idSIButton9",
    )

    def __init__(self, screenshot_dir: Path | None = None):
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise VivadoDownloadError(
                "Browser download fallback requires the 'vivado-browser' extra"
            ) from exc

        self._playwright_timeout_error = PlaywrightTimeoutError
        self._sync_playwright = sync_playwright
        self.logger = get_logger("adibuild.vivado.browser")
        
        # Priority: constructor arg > env var > default home dir
        self.screenshot_dir = (
            screenshot_dir 
            or Path(os.environ.get("ADIBUILD_VIVADO_DEBUG_DIR", ""))
            if os.environ.get("ADIBUILD_VIVADO_DEBUG_DIR")
            else Path.home() / ".adibuild" / "toolchains" / "vivado" / "debug"
        )

    def _take_screenshot(self, page, name: str) -> None:
        """Capture a browser screenshot for debugging."""
        try:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            path = self.screenshot_dir / f"{timestamp}-{name}.png"
            page.screenshot(path=path)
            self.logger.info(f"Captured debug screenshot: {path}")
        except Exception as exc:
            self.logger.warning(f"Failed to capture debug screenshot '{name}': {exc}")

    def _dismiss_cookie_banners(self, page) -> None:
        """Dismiss or hide cookie consent banners that block clicks."""
        try:
            # Try clicking common buttons first
            selectors = (
                "#onetrust-accept-btn-handler",
                "#onetrust-close-btn-handler",
                "button:has-text('Accept All Cookies')",
                "button:has-text('Accept Cookies')",
            )
            for sel in selectors:
                loc = page.locator(sel).first
                if loc.count() and loc.is_visible():
                    self.logger.info(f"Dismissing cookie banner with selector: {sel}")
                    loc.click()
                    page.wait_for_timeout(1000)
                    return

            # If clicking didn't work or banner is still there, aggressively hide it via CSS
            self.logger.info("Aggressively hiding cookie banners via script")
            page.evaluate("""
                () => {
                    const ids = ['onetrust-consent-sdk', 'onetrust-pc-dark-filter', 'onetrust-banner-sdk'];
                    ids.forEach(id => {
                        const el = document.getElementById(id);
                        if (el) el.style.display = 'none';
                    });
                    const classes = ['onetrust-pc-dark-filter', 'ot-sdk-container', 'ot-sdk-row'];
                    classes.forEach(cls => {
                        const elements = document.getElementsByClassName(cls);
                        for (let el of elements) el.style.display = 'none';
                    });
                }
            """)
            page.wait_for_timeout(1000)
        except Exception as e:
            self.logger.warning(f"Error while dismissing cookie banner: {e}")

    def _fill_download_form_if_needed(self, page) -> object | None:
        """Fill the mandatory AMD export control form if it appears."""
        try:
            # Dismiss banners that might block fields
            self._dismiss_cookie_banners(page)
            
            # Wait a bit for the form to actually appear
            page.wait_for_timeout(5000)
            
            self.logger.info(f"Checking for AMD export control form at {page.url}")
            
            # Log all visible inputs to help debug
            try:
                all_inputs = page.locator("input, select").all()
                visible_names = [f"{i.get_attribute('name') or i.get_attribute('id') or 'none'}({i.get_attribute('type') or 'select'})" 
                                 for i in all_inputs if i.is_visible()]
                self.logger.info(f"Visible inputs on page: {visible_names}")
            except Exception:
                pass

            # Common fields in the AMD download form
            form_fields = {
                "First_Name": "Travis",
                "Last_Name": "Collins",
                "Company": "Analog Devices Inc",
                "Address_1": "804 Woburn Street",
                "Address_2": "N/A",
                "City": "Wilmington",
                "Zip_Code": "01887",
                "Job_Function": "Other",
                "Country": "United States",
                "State": "Massachusetts",
                "Email": "travis.collins@analog.com",
                "Phone": "9786585555",
            }

            filled_any = False
            
            # Try to find and fill fields in the main page and all frames
            for frame in page.frames:
                # Use JS to fill values directly
                try:
                    js_fill = f"""
                        () => {{
                            const fields = {json.dumps(form_fields)};
                            let filled = false;
                            
                            // 1. Fill by Name/ID
                            for (const [name, value] of Object.entries(fields)) {{
                                const elements = document.querySelectorAll(`[name="${{name}}"], [id="${{name}}"], [id*="${{name}}"]`);
                                elements.forEach(el => {{
                                    if (el.tagName === 'SELECT') {{
                                        const option = Array.from(el.options).find(opt => 
                                            opt.text.toLowerCase().includes(value.toLowerCase()) || 
                                            opt.value.toLowerCase().includes(value.toLowerCase())
                                        );
                                        if (option) {{
                                            el.value = option.value;
                                        }} else if (el.options.length > 1) {{
                                            el.selectedIndex = 1; // Pick something
                                        }}
                                    }} else {{
                                        el.value = value;
                                    }}
                                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    filled = true;
                                }});
                            }}
                            
                            // 2. Aggressive Checkbox/Radio checking (will be followed by click in Playwright)
                            return filled;
                        }}
                    """
                    if frame.evaluate(js_fill):
                        self.logger.info(f"Filled form fields via aggressive JS in frame {frame.name or 'main'}")
                        filled_any = True
                        
                        # Use Playwright click for checkboxes to trigger events correctly
                        try:
                            checkboxes = frame.locator("input[type='checkbox']").all()
                            for cb in checkboxes:
                                if cb.is_visible() and not cb.is_checked():
                                    cb.click(force=True)
                                    page.wait_for_timeout(500)
                        except Exception:
                            pass
                except Exception as e:
                    self.logger.warning(f"Error filling form via aggressive JS in frame {frame.name or 'main'}: {e}")

                if filled_any:
                    self._take_screenshot(page, "download-form-filled")
                    # Submit the form
                    self._dismiss_cookie_banners(page)
                    
                    try:
                        self.logger.info(f"Submitting AMD download form via JS in frame {frame.name or 'main'}")
                        # Setup download listener
                        with page.expect_download(timeout=120000) as download_info:
                            # Try multiple JS submission styles
                            frame.evaluate("""
                                () => {
                                    const form = document.forms[0];
                                    if (form) {
                                        form.submit();
                                    } else {
                                        const btn = document.querySelector('input[type="submit"], button[type="submit"], #submit');
                                        if (btn) btn.click();
                                    }
                                }
                            """)
                        self.logger.info("Download triggered by aggressive form submission (JS)")
                        return download_info.value
                    except Exception as e:
                        self.logger.info(f"Aggressive JS submission did not trigger download: {e}. Trying UI click.")
                        self._take_screenshot(page, "download-submission-js-failed")
                        
                        submit_selectors = (
                            "input[type='submit']", 
                            "button[type='submit']", 
                            "#submit",
                            "input[value='Download']",
                            "button:has-text('Download')"
                        )
                        submit = None
                        for sel in submit_selectors:
                            try:
                                loc = frame.locator(sel).first
                                if loc.count() and loc.is_visible():
                                    submit = loc
                                    break
                            except Exception:
                                continue

                        if submit:
                            try:
                                with page.expect_download(timeout=120000) as download_info:
                                    submit.click(force=True)
                                self.logger.info("Download triggered by form submission (click with force)")
                                return download_info.value
                            except Exception as e2:
                                self.logger.info(f"UI click did not trigger download: {e2}")
                                self._take_screenshot(page, "download-submission-failed")
                                
                                # Check for error messages on page
                                try:
                                    errors = frame.locator(".error, .errormsg, .alert-danger, [id*='error']").all()
                                    if errors:
                                        err_texts = [e.inner_text() for e in errors if e.is_visible()]
                                        self.logger.warning(f"Detected potential form errors: {err_texts}")
                                except Exception:
                                    pass
                                    
                                try:
                                    page.wait_for_load_state("domcontentloaded", timeout=60000)
                                except Exception:
                                    pass
                    # If we filled fields in this frame, we probably don't need to check others
                    break

        except Exception as exc:
            self.logger.warning(f"Error while filling AMD download form: {exc}")
        return None

    def download(
        self,
        release: VivadoRelease,
        destination: Path,
        credentials: VivadoCredentials,
    ) -> Path:
        """Login to AMD and download the installer."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.logger.info(
            f"Starting browser-authenticated AMD download for {release.filename}"
        )

        with self._sync_playwright() as playwright:
            self.logger.info("Launching Chromium for AMD download")
            browser = playwright.chromium.launch(**self._launch_options())
            context = browser.new_context(
                accept_downloads=True,
                ignore_https_errors=True,
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                device_scale_factor=1,
            )
            page = context.new_page()

            # Apply playwright-stealth if available
            try:
                from playwright_stealth import stealth
                stealth(page)
                self.logger.info("Applied playwright-stealth to the page")
            except ImportError:
                pass

            # Human-like delay before initial navigation
            page.wait_for_timeout(2000)

            auth_url = self._auth_bootstrap_url(release)
            self.logger.info(f"Opening AMD login/bootstrap page {auth_url}")
            try:
                self._goto_with_retry(
                    page,
                    auth_url,
                    "browser-login-navigation",
                    credentials=credentials,
                    settle_dom=True,
                    wait_until="networkidle",
                )
                self._login_if_needed(page, credentials)
            except Exception as e:
                self.logger.warning(f"Initial navigation/login was not clean, but we will check for download form: {e}")
            
            self.logger.info("Waiting for browser-authenticated AMD installer download to start")
            # Use a list to store the download object from the event handler
            downloads = []
            page.on("download", lambda d: downloads.append(d))

            # 1. Try filling the form (often triggers download on submit)
            self._fill_download_form_if_needed(page)
            
            # 2. If not triggered by form, try to find a link that looks like the installer
            if not downloads:
                self.logger.info("Checking for download links on page")
                link = page.locator(f"a[href*='{release.filename}'], a:has-text('{release.version}'), a:has-text('Linux Self-extracting')").first
                if link.count() > 0 and link.is_visible():
                    self.logger.info(f"Clicking download link: {link.get_attribute('href')}")
                    link.click()

            # 3. Last resort: direct navigation
            if not downloads:
                self.logger.info(f"Triggering download via direct navigation to {release.download_url}")
                page.wait_for_timeout(10000)
                page.goto(release.download_url, wait_until="commit", timeout=120000)

            # Wait for the download event to be captured
            start_wait = time.time()
            while not downloads and time.time() - start_wait < 60:
                page.wait_for_timeout(1000)
            
            if not downloads:
                 raise VivadoDownloadError("Could not trigger or detect Vivado download start after 60s")

            download = downloads[0]
            suggested_name = download.suggested_filename or release.filename
            target = destination
            if destination.name != suggested_name:
                target = destination.parent / suggested_name

            download.save_as(str(target))
            self.logger.info(f"Saved browser-authenticated AMD download to {target}")
            context.close()
            browser.close()
            return target

    @staticmethod
    def _auth_bootstrap_url(release: VivadoRelease) -> str:
        """Choose a stable landing page for browser-based authentication."""
        return f"https://account.amd.com/en/forms/downloads/xef.html?filename={release.filename}"

    @staticmethod
    def _launch_options() -> dict[str, object]:
        """Return browser launch options that work in containerized environments."""
        headless = os.environ.get("ADIBUILD_BROWSER_HEADLESS", "1").lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        options: dict[str, object] = {
            "headless": headless,
            "args": [
                "--disable-http2",
                "--disable-blink-features=AutomationControlled",
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        }
        geteuid = getattr(os, "geteuid", None)
        if geteuid is not None and geteuid() == 0:
            options["args"].append("--no-sandbox")
        return options

    def _login_if_needed(
        self, page, credentials: VivadoCredentials  # pragma: no cover - mocked in tests
    ) -> None:
        """Fill common AMD/Microsoft-style login forms with human-like delays."""
        try:
            self.logger.info(f"Checking for login forms at {page.url} (title='{page.title()}')")
            
            # Step 1: Username
            email_locator = self._first_visible(page, self.EMAIL_SELECTORS)
            if email_locator:
                self.logger.info("Detected AMD login email prompt; submitting username")
                self._take_screenshot(page, "login-email-prompt")
                page.wait_for_timeout(1000 + (int(os.urandom(1)[0]) % 2000))
                email_locator.fill(credentials.username)
                page.wait_for_timeout(500 + (int(os.urandom(1)[0]) % 1000))
                self._click_first(page, self.SUBMIT_SELECTORS)
                page.wait_for_load_state("domcontentloaded", timeout=60000)
                self.logger.info(f"Submitted email; now at {page.url}")
                self._take_screenshot(page, "login-email-submitted")

            # Step 2: Password (might be on same page or next)
            # Wait for potential redirects or dynamic password field loading
            page.wait_for_timeout(2000 + (int(os.urandom(1)[0]) % 2000))

            password_locator = self._first_visible(page, self.PASSWORD_SELECTORS)
            if password_locator:
                self.logger.info(
                    "Detected AMD login password prompt; submitting password"
                )
                self._take_screenshot(page, "login-password-prompt")
                
                # If username is also visible here, fill it too if not already done
                # (Some SAML/Okta forms show both at once)
                if not email_locator:
                     e_loc = self._first_visible(page, self.EMAIL_SELECTORS)
                     if e_loc:
                         e_loc.fill(credentials.username)

                page.wait_for_timeout(1000 + (int(os.urandom(1)[0]) % 2000))
                password_locator.fill(credentials.password)
                page.wait_for_timeout(500 + (int(os.urandom(1)[0]) % 1000))
                self._click_first(page, self.SUBMIT_SELECTORS)
                
                # After password, we might see a "Stay signed in?" prompt (Microsoft)
                # or just the final redirect.
                page.wait_for_timeout(2000 + (int(os.urandom(1)[0]) % 2000))
                stay_signed_in = self._first_visible(page, ("input[value='Yes']", "#idSIButton9"))
                if stay_signed_in:
                    self.logger.info("Detected 'Stay signed in?' prompt; clicking Yes")
                    stay_signed_in.click()
                    page.wait_for_load_state("domcontentloaded", timeout=60000)

                self.logger.info(f"Submitted password; now at {page.url}")
                self._take_screenshot(page, "login-password-submitted")
            else:
                self.logger.info(f"No browser login form detected at {page.url}")
                self._take_screenshot(page, "login-form-not-found")
        except Exception as exc:  # pragma: no cover - integration-only timing
            raise VivadoDownloadError(
                f"Vivado download failed at stage=browser-login-submit: {exc}"
            ) from exc

    def _goto_with_retry(
        self,
        page,
        url: str,
        stage: str,
        credentials: VivadoCredentials | None = None,
        settle_dom: bool = False,
        wait_until: str = "domcontentloaded",
    ) -> None:
        """Navigate with retries for flaky AMD/Xilinx endpoints."""
        last_exc = None
        for attempt in range(1, 4):
            try:
                self.logger.info(
                    f"Browser navigation stage={stage} attempt {attempt}/3 to {url}"
                )
                # Human-like delay before navigation to avoid rate-limiting
                page.wait_for_timeout(2000 + (int(os.urandom(1)[0]) % 3000))

                if stage == "browser-login-navigation":
                    self.logger.info("Special wait for login fields on navigation")
                    # We start the navigation and then wait for either the timeout or the element
                    try:
                        page.goto(url, wait_until="commit", timeout=120000)
                    except:
                        pass
                    
                    self.logger.info("Waiting 10s for page to render...")
                    page.wait_for_timeout(10000)
                    self._take_screenshot(page, "login-navigation-start")
                    
                    # Wait for one of the email selectors or a general sign-in marker
                    if credentials:
                        try:
                            self.logger.info("Waiting for email field or redirect to settle...")
                            email_el = page.wait_for_selector(
                                "input[name='loginfmt'], input[type='email'], #i0116, input[name='identifier']",
                                state="visible",
                                timeout=60000
                            )
                            if email_el:
                                self.logger.info(f"Filling email: {credentials.username}")
                                email_el.click()
                                # Use insert_text to bypass some event listeners
                                try:
                                    page.keyboard.insert_text(credentials.username)
                                except:
                                    page.keyboard.type(credentials.username, delay=50)
                                
                                page.keyboard.press("Enter")
                                page.wait_for_timeout(2000)
                                
                                # Wait for password
                                pwd_el = page.wait_for_selector(
                                    "input[name='password'], input[type='password'], #i0118, input[name='credentials.passcode']",
                                    state="visible",
                                    timeout=60000
                                )
                                if pwd_el:
                                    self.logger.info("Filling password")
                                    pwd_el.click()
                                    try:
                                        page.keyboard.insert_text(credentials.password)
                                    except:
                                        page.keyboard.type(credentials.password, delay=50)
                                    
                                    page.keyboard.press("Enter")
                                    page.wait_for_timeout(5000)

                        except Exception as e:
                            self.logger.warning(f"Did not see standard login fields yet: {e}")
                            self.logger.info(f"Current URL: {page.url}")
                            self.logger.info(f"Current Title: {page.title()}")
                            self._take_screenshot(page, "login-wait-fail")
                            # Try to log what it DOES see
                            try:
                                inputs = page.locator("input").all()
                                self.logger.info(f"Visible inputs: {[i.get_attribute('name') or i.get_attribute('id') for i in inputs if i.is_visible()]}")
                            except Exception:
                                pass
                            
                            # Last ditch: log the body text
                            try:
                                body_text = page.locator("body").inner_text()
                                # Only log first 500 chars
                                self.logger.info(f"Page body text snippet: {body_text[:500]}...")
                            except Exception:
                                pass

                else:
                    response = page.goto(url, wait_until=wait_until, timeout=120000)
                    if response:
                        self.logger.info(
                            f"Browser navigation stage={stage} response status={response.status} "
                            f"url={page.url} title='{page.title()}'"
                        )
                if settle_dom:
                    try:
                        page.wait_for_load_state("domcontentloaded", timeout=60000)
                    except Exception as exc:  # pragma: no cover - integration-only timing
                        self.logger.info(
                            f"Browser navigation stage={stage} committed but did not reach "
                            f"domcontentloaded within 30s: {exc}"
                        )
                return
            except Exception as exc:  # pragma: no cover - exercised in integration
                last_exc = exc
                current_url = page.url
                try:
                    current_title = page.title()
                except Exception:
                    current_title = "unknown"
                self.logger.warning(
                    f"Browser navigation failed at stage={stage} attempt {attempt}/3: {exc} "
                    f"(current_url={current_url} current_title='{current_title}')"
                )
                self._take_screenshot(page, f"fail-{stage}-attempt-{attempt}")
                if attempt < 3:
                    page.wait_for_timeout(3000)

        raise VivadoDownloadError(
            f"Vivado download failed at stage={stage}: browser navigation to {url} "
            f"failed after 3 attempts with {last_exc}"
        ) from last_exc

    def _session_from_browser_context(self, context, page) -> requests.Session:
        """Build a requests session from authenticated browser cookies."""
        session = requests.Session()
        for cookie in context.cookies():
            session.cookies.set(
                cookie["name"],
                cookie["value"],
                domain=cookie.get("domain"),
                path=cookie.get("path", "/"),
            )

        try:
            user_agent = page.evaluate("() => navigator.userAgent")
        except Exception:
            user_agent = None
        if user_agent:
            session.headers.update({"User-Agent": user_agent})
        return session

    @staticmethod
    def _first_visible(page, selectors):
        for selector in selectors:
            locator = page.locator(selector).first
            if locator.count() and locator.is_visible():
                return locator
        return None

    @staticmethod
    def _click_first(page, selectors):
        locator = PlaywrightDownloadStrategy._first_visible(page, selectors)
        if locator:
            locator.click()


class VivadoInstaller:
    """Download, verify, and install AMD Vivado on Linux."""

    AGREEMENTS = ("XilinxEULA", "3rdPartyEULA", "WebTalkTerms")
    BROWSER_AUTH_HOST_MARKERS = ("account.amd.com", "www.xilinx.com/member/forms")

    def __init__(
        self,
        cache_dir: Path | None = None,
        release_catalog: dict[str, VivadoRelease] | None = None,
    ):
        self.cache_dir = cache_dir or Path.home() / ".adibuild" / "toolchains" / "vivado"
        self.release_catalog = release_catalog or SUPPORTED_RELEASES
        self.logger = get_logger("adibuild.vivado")

    def list_supported_releases(self) -> list[VivadoRelease]:
        """Return unique supported releases."""
        seen = set()
        releases = []
        for release in self.release_catalog.values():
            if release.version not in seen:
                releases.append(release)
                seen.add(release.version)
        return sorted(releases, key=lambda item: item.version)

    def resolve_release(self, version: str) -> VivadoRelease:
        """Resolve a user-requested version to installer metadata."""
        if version not in self.release_catalog:
            supported = ", ".join(rel.version for rel in self.list_supported_releases())
            raise VivadoDownloadError(
                f"Unsupported Vivado version '{version}'. Supported versions: {supported}"
            )
        release = self.release_catalog[version]
        self.logger.info(
            "Resolved Vivado release "
            f"{version} -> installer {release.installer_version} "
            f"({release.filename})"
        )
        return release

    def download_installer(
        self,
        version: str,
        cache_dir: Path | None = None,
        credentials: VivadoCredentials | None = None,
        max_attempts: int = 3,
    ) -> Path:
        """Download the self-extracting Linux web installer."""
        release = self.resolve_release(version)
        cache_root = cache_dir or self.cache_dir / "installers"
        installer_path = cache_root / release.filename

        if installer_path.exists():
            self.logger.info(f"Using cached Vivado installer at {installer_path}")
            self.verify_installer(release, installer_path)
            return installer_path

        for attempt in range(1, max_attempts + 1):
            try:
                from adibuild.core.docker import DockerError
                if attempt > 1:
                    self.logger.info(
                        f"Retrying Vivado download (attempt {attempt}/{max_attempts})"
                    )
                    # Exponential backoff
                    delay = 15 * (2 ** (attempt - 2))
                    self.logger.info(f"Waiting {delay}s before retry...")
                    time.sleep(delay)

                return self._download_with_fallback(release, installer_path, credentials)
            except (VivadoDownloadError, DockerError) as e:
                if attempt == max_attempts:
                    self.logger.error(
                        f"Vivado download failed after {max_attempts} attempts: {e}"
                    )
                    raise
                self.logger.warning(f"Download attempt {attempt} failed: {e}")

        # Should not reach here
        raise VivadoDownloadError("Vivado download failed")

    def _download_with_fallback(
        self,
        release: VivadoRelease,
        installer_path: Path,
        credentials: VivadoCredentials | None,
    ) -> Path:
        """Execute download strategies in order of preference."""
        # Try Docker first (most robust)
        try:
            from adibuild.core.docker import DockerError
            if self._prefer_browser_download(release, credentials):
                self.logger.info("Using Docker for authenticated download")
                installer_path = DockerDownloadStrategy().download(
                    release, installer_path, credentials
                )
                self.verify_installer(release, installer_path)
                installer_path.chmod(installer_path.stat().st_mode | 0o111)
                return installer_path
        except (ImportError, DockerError, VivadoDownloadError) as e:
            self.logger.debug(f"Docker download strategy failed: {e}")

        # Try Session Extraction next (Login via browser, download via requests)
        try:
            if self._prefer_browser_download(release, credentials):
                self.logger.info("Using Session Extraction for authenticated download")
                installer_path = SessionDownloadStrategy().download(
                    release, installer_path, credentials
                )
                self.verify_installer(release, installer_path)
                installer_path.chmod(installer_path.stat().st_mode | 0o111)
                return installer_path
        except (ImportError, VivadoDownloadError) as e:
            self.logger.debug(f"Session extraction download strategy failed: {e}")

        # Try Playwright next
        try:
            strategy = PlaywrightDownloadStrategy()
            if self._prefer_browser_download(release, credentials):
                self.logger.info("Using Playwright for authenticated download")
                installer_path = strategy.download(release, installer_path, credentials)
                self.verify_installer(release, installer_path)
                installer_path.chmod(installer_path.stat().st_mode | 0o111)
                return installer_path
        except (ImportError, VivadoDownloadError) as e:
            self.logger.debug(f"Playwright download strategy failed: {e}")

        # Try Selenium next
        try:
            strategy = SeleniumDownloadStrategy()
            if self._prefer_browser_download(release, credentials):
                self.logger.info("Using Selenium for authenticated download")
                installer_path = strategy.download(release, installer_path, credentials)
                self.verify_installer(release, installer_path)
                installer_path.chmod(installer_path.stat().st_mode | 0o111)
                return installer_path
        except (ImportError, VivadoDownloadError) as e:
            self.logger.debug(f"Selenium download strategy failed: {e}")

        try:
            RequestsDownloadStrategy().download(release, installer_path)
        except VivadoAuthRequiredError:
            if not credentials:
                raise

            self.logger.info("Falling back to authenticated browser download")
            # Try Docker first in fallback too if credentials provided
            try:
                from adibuild.core.docker import DockerError
                return DockerDownloadStrategy().download(
                    release, installer_path, credentials
                )
            except (ImportError, DockerError, VivadoDownloadError):
                try:
                    return SessionDownloadStrategy().download(
                        release, installer_path, credentials
                    )
                except (ImportError, VivadoDownloadError):
                    try:
                        return PlaywrightDownloadStrategy().download(
                            release, installer_path, credentials
                        )
                    except (ImportError, VivadoDownloadError):
                        return SeleniumDownloadStrategy().download(
                            release, installer_path, credentials
                        )

        self.verify_installer(release, installer_path)
        installer_path.chmod(installer_path.stat().st_mode | 0o111)
        self.logger.info(f"Vivado installer ready at {installer_path}")
        return installer_path

    def _prefer_browser_download(
        self,
        release: VivadoRelease,
        credentials: VivadoCredentials | None,
    ) -> bool:
        """Decide whether to skip direct HTTP download and use browser auth first."""
        if not credentials:
            return False

        download_url = release.download_url.lower()
        return any(marker in download_url for marker in self.BROWSER_AUTH_HOST_MARKERS)

    def verify_installer(self, release: VivadoRelease, installer_path: Path) -> None:
        """Verify the installer against AMD-published digests when available."""
        if os.environ.get("ADIBUILD_VIVADO_SKIP_VERIFY", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }:
            self.logger.warning(
                f"Skipping Vivado installer verification for {installer_path} "
                "because ADIBUILD_VIVADO_SKIP_VERIFY is set"
            )
            return

        if not installer_path.exists():
            raise VivadoDownloadError(f"Installer not found: {installer_path}")

        if not release.digests_url:
            self.logger.info(
                f"No digest URL published for {release.filename}; skipping verification"
            )
            return

        digest_map = self._fetch_digest_map(release)
        sha256 = digest_map.get("sha256")
        if not sha256:
            self.logger.info(
                f"No SHA256 digest found for {release.filename}; skipping verification"
            )
            return

        actual_sha256 = self._hash_file(installer_path, "sha256")
        if actual_sha256 != sha256:
            raise VivadoDownloadError(
                f"Digest mismatch for {installer_path.name}: expected {sha256}, "
                f"got {actual_sha256}"
            )
        self.logger.info(f"Verified SHA256 for {installer_path.name}")

    def install(self, request: VivadoInstallRequest) -> VivadoInstallResult:
        """Install a supported Vivado release via the web installer client."""
        release = self.resolve_release(request.version)
        credentials = request.credentials or VivadoCredentials.from_env()
        self.logger.info(
            f"Starting Vivado install for {release.version} into {request.install_dir}"
        )
        installer_path = request.installer_path
        if installer_path is None:
            installer_path = self.download_installer(
                release.version,
                cache_dir=request.cache_dir,
                credentials=credentials,
            )
        else:
            self.logger.info(f"Using caller-provided installer at {installer_path}")
            self.verify_installer(release, installer_path)
            self._ensure_executable(installer_path)

        extract_dir = self.extract_web_installer(
            release=release,
            installer_path=installer_path,
            extract_dir=request.extract_dir,
        )
        xsetup = self._find_xsetup(extract_dir)

        if request.config_path is None and credentials is None:
            raise VivadoInstallError(
                "Vivado web installation requires AMD_USERNAME/AMD_PASSWORD "
                "or explicit credentials"
            )

        if credentials is not None:
            self.logger.info("Generating AMD installer authentication token")
            self.acquire_auth_token(xsetup, credentials)
        else:
            self.logger.info(
                "Skipping token generation because a config file was provided"
            )

        self.logger.info(
            f"Running Vivado batch installer from {xsetup.parent} "
            f"to target root {request.install_dir}"
        )
        self.run_install(
            release=release,
            xsetup=xsetup,
            install_dir=request.install_dir,
            config_path=request.config_path,
            edition=request.edition or release.edition,
            agree_webtalk_terms=request.agree_webtalk_terms,
        )

        toolchain = self.status(release.version, request.install_dir)
        if toolchain is None:
            raise VivadoInstallError(
                f"Vivado {release.install_version} was installed but could not be detected"
            )
        self.logger.info(
            f"Detected installed Vivado {toolchain.version} at {toolchain.path}"
        )

        return VivadoInstallResult(
            release=release,
            installer_path=installer_path,
            extract_dir=extract_dir,
            toolchain=toolchain,
        )

    def _ensure_executable(self, path: Path) -> None:
        """Ensure an installer binary is executable without failing on read-only mounts."""
        if os.access(path, os.X_OK):
            return

        try:
            path.chmod(path.stat().st_mode | 0o111)
        except OSError as exc:
            if os.access(path, os.X_OK):
                return
            raise VivadoInstallError(
                f"Could not mark installer executable: {path}: {exc}"
            ) from exc

    def status(
        self,
        version: str | None = None,
        install_dir: Path | None = None,
    ) -> ToolchainInfo | None:
        """Detect an installed Vivado release, optionally scoped to a root directory."""
        from adibuild.core.toolchain import VivadoToolchain

        search_paths = None
        if install_dir and version:
            release = self.resolve_release(version)
            search_paths = [
                install_dir / "Vivado" / release.install_version,
                install_dir / "Vitis" / release.install_version,
                install_dir / release.install_version / "Vivado",
                install_dir / release.install_version / "Vitis",
            ]
        elif install_dir:
            search_paths = []
            for product in ("Vivado", "Vitis"):
                product_root = install_dir / product
                if product_root.exists():
                    search_paths.extend(
                        path for path in product_root.iterdir() if path.is_dir()
                    )
            for version_root in (install_dir.iterdir() if install_dir.exists() else []):
                if not version_root.is_dir():
                    continue
                search_paths.extend(
                    candidate
                    for candidate in (
                        version_root / "Vivado",
                        version_root / "Vitis",
                    )
                    if candidate.exists()
                )

        if search_paths is not None:
            self.logger.info(
                "Checking Vivado installation status in: "
                + ", ".join(str(path) for path in search_paths)
            )
        elif version:
            self.logger.info(f"Checking Vivado installation status for version {version}")
        else:
            self.logger.info(
                "Checking Vivado installation status in default search paths"
            )

        toolchain = VivadoToolchain(
            search_paths=search_paths,
            preferred_version=version,
            strict_version=bool(version),
        )
        return toolchain.detect()

    def extract_web_installer(
        self,
        release: VivadoRelease,
        installer_path: Path,
        extract_dir: Path | None = None,
    ) -> Path:
        """Extract the batch client out of the self-extracting installer."""
        target_dir = extract_dir or self.cache_dir / "extracted" / release.version
        target_dir.mkdir(parents=True, exist_ok=True)

        xsetup = self._find_xsetup(target_dir, required=False)
        if xsetup is not None:
            self.logger.info(f"Using cached extracted installer client at {target_dir}")
            return target_dir

        self.logger.info(f"Extracting Vivado installer into {target_dir}")
        cmd = [
            str(installer_path),
            "--keep",
            "--noexec",
            "--target",
            str(target_dir),
        ]
        self._run_command(cmd, check=True)
        self.logger.info(f"Extracted Vivado installer into {target_dir}")
        return target_dir

    def acquire_auth_token(
        self, xsetup: Path, credentials: VivadoCredentials
    ) -> subprocess.CompletedProcess:
        """Generate a short-lived authentication token for the web installer."""
        input_data = f"{credentials.username}\n{credentials.password}\n"
        return self._run_command(
            [str(xsetup), "-b", "AuthTokenGen"],
            cwd=xsetup.parent,
            input_data=input_data,
            check=True,
            redact_output=True,
        )

    def run_install(
        self,
        release: VivadoRelease,
        xsetup: Path,
        install_dir: Path,
        config_path: Path | None,
        edition: str,
        agree_webtalk_terms: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run the extracted installer client in batch mode."""
        agreements = list(self.AGREEMENTS[:2])
        if agree_webtalk_terms:
            agreements.append(self.AGREEMENTS[2])

        cmd = [
            str(xsetup),
            "-b",
            "Install",
            "-a",
            ",".join(agreements),
        ]
        if config_path:
            cmd.extend(["-c", str(config_path)])
        else:
            cmd.extend(["--edition", edition, "--location", str(install_dir)])

        install_dir.mkdir(parents=True, exist_ok=True)
        return self._run_command(cmd, cwd=xsetup.parent, check=True)

    def _fetch_digest_map(self, release: VivadoRelease) -> dict[str, str]:
        self.logger.info(f"Fetching official digests from {release.digests_url}")
        response = requests.get(release.digests_url, timeout=120)
        response.raise_for_status()

        digest_map = {}
        algo_order = ("md5", "sha1", "sha256", "sha512")
        for line in response.text.splitlines():
            match = re.match(r"([a-fA-F0-9]{32,128})\s+\*?(.+)$", line.strip())
            if not match:
                continue
            digest = match.group(1).lower()
            filename = Path(match.group(2)).name
            if filename != release.filename:
                continue

            if len(digest) == 32:
                digest_map[algo_order[0]] = digest
            elif len(digest) == 40:
                digest_map[algo_order[1]] = digest
            elif len(digest) == 64:
                digest_map[algo_order[2]] = digest
            elif len(digest) == 128:
                digest_map[algo_order[3]] = digest

        return digest_map

    @staticmethod
    def _hash_file(path: Path, algorithm: str) -> str:
        hasher = hashlib.new(algorithm)
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def _find_xsetup(root: Path, required: bool = True) -> Path | None:
        direct = root / "xsetup"
        if direct.exists():
            return direct

        candidates = list(root.rglob("xsetup"))
        if candidates:
            return candidates[0]

        if required:
            raise VivadoInstallError(f"Could not find xsetup under {root}")
        return None

    def _run_command(
        self,
        cmd: list[str],
        cwd: Path | None = None,
        input_data: str | None = None,
        check: bool = False,
        redact_output: bool = False,
    ) -> subprocess.CompletedProcess:
        self.logger.info(f"Running command: {' '.join(shlex_quote(arg) for arg in cmd)}")
        
        # We use Popen to stream output for long-running installer steps
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdin=subprocess.PIPE if input_data else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        stdout_lines = []
        if input_data:
            process.stdin.write(input_data)
            process.stdin.close()

        # Stream output to logger in real-time
        if not redact_output:
            for line in process.stdout:
                line = line.rstrip()
                stdout_lines.append(line)
                self.logger.info(line)
        else:
            # Still read it so we don't hang, but don't log it
            for line in process.stdout:
                stdout_lines.append(line)
                if "error" in line.lower() or "fail" in line.lower():
                     # Log errors even in redacted mode if possible (risky for creds though)
                     # For now, let's just keep it simple and not log anything if redacted
                     pass

        return_code = process.wait()
        stdout = "\n".join(stdout_lines)

        if return_code != 0 and check:
            err_stdout = stdout
            if redact_output:
                err_stdout = "<redacted>"
            raise VivadoInstallError(
                f"Command failed with exit code {return_code}: "
                f"{' '.join(shlex_quote(arg) for arg in cmd)}\n"
                f"stdout: {err_stdout}"
            )
        
        if redact_output:
            if stdout.strip():
                self.logger.info("Command output redacted")
            return subprocess.CompletedProcess(cmd, return_code, stdout=stdout, stderr="")

        return subprocess.CompletedProcess(cmd, return_code, stdout=stdout, stderr="")


def shlex_quote(value: str) -> str:
    """Quote command arguments for logs without importing shlex at module load."""
    import shlex

    return shlex.quote(value)
