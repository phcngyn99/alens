"""Login Page Object."""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage


class LoginPage(BasePage):
    """Page object for the login page."""
    
    # Locators
    USERNAME_INPUT = (By.CSS_SELECTOR, "input[type='text'], input[name='username']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[type='password']")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".text-red-500, .error-message, [role='alert']")
    PAGE_TITLE = (By.CSS_SELECTOR, "h1, h2")
    
    def navigate(self):
        """Navigate to the login page."""
        super().navigate("/login")
    
    def enter_username(self, username: str):
        """Enter username."""
        self.type_text(self.USERNAME_INPUT, username)
    
    def enter_password(self, password: str):
        """Enter password."""
        self.type_text(self.PASSWORD_INPUT, password)
    
    def click_login(self):
        """Click the login button."""
        self.click(self.LOGIN_BUTTON)
    
    def login(self, username: str, password: str):
        """Perform complete login action."""
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()
    
    def wait_for_redirect(self, wait: WebDriverWait = None, timeout: int = 10):
        """Wait for redirect after successful login."""
        if wait:
            wait.until(EC.url_contains("/connections"))
        else:
            self.wait_for_url_contains("/connections", timeout)
    
    def get_error_message(self) -> str:
        """Get the error message if login fails."""
        try:
            return self.get_text(self.ERROR_MESSAGE)
        except:
            return ""
    
    def is_login_page(self) -> bool:
        """Check if we're on the login page."""
        return "/login" in self.get_current_url() or self.is_element_present(self.LOGIN_BUTTON)
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in (redirected away from login)."""
        return "/login" not in self.get_current_url()

