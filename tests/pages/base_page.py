"""Base Page Object class with common functionality."""
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


class BasePage:
    """Base class for all page objects."""
    
    def __init__(self, driver: WebDriver, base_url: str):
        self.driver = driver
        self.base_url = base_url
        self.timeout = 20
    
    def navigate(self, path: str = ""):
        """Navigate to a specific path."""
        url = f"{self.base_url}{path}"
        self.driver.get(url)
    
    def wait_for_element(self, locator: tuple, timeout: int = None) -> bool:
        """Wait for an element to be present."""
        timeout = timeout or self.timeout
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False
    
    def wait_for_element_visible(self, locator: tuple, timeout: int = None):
        """Wait for an element to be visible and return it."""
        timeout = timeout or self.timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )
    
    def wait_for_element_clickable(self, locator: tuple, timeout: int = None):
        """Wait for an element to be clickable and return it."""
        timeout = timeout or self.timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
    
    def wait_for_text_in_element(self, locator: tuple, text: str, timeout: int = None) -> bool:
        """Wait for specific text to appear in an element."""
        timeout = timeout or self.timeout
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.text_to_be_present_in_element(locator, text)
            )
            return True
        except TimeoutException:
            return False
    
    def wait_for_url_contains(self, text: str, timeout: int = None) -> bool:
        """Wait for URL to contain specific text."""
        timeout = timeout or self.timeout
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.url_contains(text)
            )
            return True
        except TimeoutException:
            return False
    
    def find_element(self, locator: tuple):
        """Find a single element."""
        return self.driver.find_element(*locator)
    
    def find_elements(self, locator: tuple):
        """Find multiple elements."""
        return self.driver.find_elements(*locator)
    
    def get_text(self, locator: tuple) -> str:
        """Get text from an element."""
        return self.find_element(locator).text
    
    def click(self, locator: tuple):
        """Click an element."""
        self.wait_for_element_clickable(locator).click()
    
    def type_text(self, locator: tuple, text: str, clear: bool = True):
        """Type text into an input field."""
        element = self.wait_for_element_visible(locator)
        if clear:
            element.clear()
        element.send_keys(text)
    
    def select_option(self, locator: tuple, value: str):
        """Select an option from a dropdown by value."""
        from selenium.webdriver.support.ui import Select
        select = Select(self.wait_for_element_visible(locator))
        select.select_by_value(value)
    
    def select_option_by_text(self, locator: tuple, text: str):
        """Select an option from a dropdown by visible text."""
        from selenium.webdriver.support.ui import Select
        select = Select(self.wait_for_element_visible(locator))
        select.select_by_visible_text(text)
    
    def is_element_present(self, locator: tuple) -> bool:
        """Check if an element is present on the page."""
        try:
            self.driver.find_element(*locator)
            return True
        except:
            return False
    
    def is_element_visible(self, locator: tuple) -> bool:
        """Check if an element is visible on the page."""
        try:
            element = self.driver.find_element(*locator)
            return element.is_displayed()
        except:
            return False
    
    def get_current_url(self) -> str:
        """Get the current URL."""
        return self.driver.current_url
    
    def take_screenshot(self, filename: str):
        """Take a screenshot and save it."""
        self.driver.save_screenshot(f"reports/{filename}")

