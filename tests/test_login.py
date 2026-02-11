"""
Test cases for user login functionality.
"""
import pytest
from pages.login_page import LoginPage
from pages.connections_page import ConnectionsPage


class TestLogin:
    """Test suite for login functionality."""
    
    def test_login_page_loads(self, driver, base_url):
        """Test that the login page loads correctly."""
        login_page = LoginPage(driver, base_url)
        login_page.navigate()
        
        assert login_page.is_login_page(), "Should be on login page"
        assert login_page.is_element_present(login_page.USERNAME_INPUT), "Username input should be present"
        assert login_page.is_element_present(login_page.PASSWORD_INPUT), "Password input should be present"
        assert login_page.is_element_present(login_page.LOGIN_BUTTON), "Login button should be present"
    
    def test_successful_login_with_default_credentials(self, driver, base_url, credentials):
        """Test successful login with default admin credentials."""
        login_page = LoginPage(driver, base_url)
        login_page.navigate()
        
        # Perform login
        login_page.login(credentials["username"], credentials["password"])
        
        # Wait for redirect
        login_page.wait_for_redirect()
        
        # Verify we're on the connections page
        assert login_page.is_logged_in(), "User should be logged in"
        assert "/connections" in driver.current_url, "Should redirect to connections page"
    
    def test_login_with_invalid_credentials(self, driver, base_url):
        """Test login with invalid credentials shows error."""
        login_page = LoginPage(driver, base_url)
        login_page.navigate()
        
        # Try to login with wrong credentials
        login_page.login("wronguser", "wrongpassword")
        
        # Wait a moment for error to appear
        import time
        time.sleep(1)
        
        # Should still be on login page or show error
        # The exact behavior depends on implementation
        current_url = driver.current_url
        assert "/login" in current_url or login_page.is_element_present(login_page.ERROR_MESSAGE), \
            "Should stay on login page or show error"
    
    def test_login_with_empty_credentials(self, driver, base_url):
        """Test that login with empty credentials doesn't proceed."""
        login_page = LoginPage(driver, base_url)
        login_page.navigate()
        
        # Try to click login without entering credentials
        login_page.click_login()
        
        # Should still be on login page
        assert login_page.is_login_page(), "Should remain on login page"
    
    def test_redirect_to_login_when_not_authenticated(self, driver, base_url):
        """Test that unauthenticated users are redirected to login."""
        # Try to access connections page directly
        driver.get(f"{base_url}/connections")
        
        # Wait for redirect
        import time
        time.sleep(2)
        
        # Should be redirected to login
        login_page = LoginPage(driver, base_url)
        assert login_page.is_login_page() or "/login" in driver.current_url, \
            "Should be redirected to login page"

