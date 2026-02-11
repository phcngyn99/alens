"""
Pytest configuration and fixtures for Alens E2E tests.
"""

import os
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://frontend")
API_URL = os.getenv("API_URL", "http://backend:8000")
DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "wnkadmin")
DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD", "wnkadmin")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
IMPLICIT_WAIT = int(os.getenv("IMPLICIT_WAIT", "10"))
EXPLICIT_WAIT = int(os.getenv("EXPLICIT_WAIT", "20"))


@pytest.fixture(scope="session")
def chrome_options():
    """Configure Chrome options for headless testing."""
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--ignore-certificate-errors")
    return options


@pytest.fixture(scope="function")
def driver(chrome_options):
    """Create a new Chrome WebDriver instance for each test."""
    # Use environment variable or default to system chromedriver
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(IMPLICIT_WAIT)
    yield driver
    driver.quit()


@pytest.fixture(scope="function")
def wait(driver):
    """Create a WebDriverWait instance."""
    return WebDriverWait(driver, EXPLICIT_WAIT)


@pytest.fixture(scope="session")
def base_url():
    """Return the base URL for the application."""
    return BASE_URL


@pytest.fixture(scope="session")
def api_url():
    """Return the API URL."""
    return API_URL


@pytest.fixture(scope="session")
def credentials():
    """Return default login credentials."""
    return {"username": DEFAULT_USERNAME, "password": DEFAULT_PASSWORD}


@pytest.fixture(scope="function")
def logged_in_driver(driver, wait, base_url, credentials):
    """Return a driver that is already logged in."""
    from pages.login_page import LoginPage

    login_page = LoginPage(driver, base_url)
    login_page.navigate()
    login_page.login(credentials["username"], credentials["password"])
    login_page.wait_for_redirect(wait)

    yield driver


def pytest_configure(config):
    """Create reports directory if it doesn't exist."""
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(reports_dir, exist_ok=True)


def pytest_html_report_title(report):
    """Set custom title for HTML report."""
    report.title = "Alens E2E Test Report"
