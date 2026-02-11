"""
Test cases for database connections functionality.
"""
import pytest
from pages.login_page import LoginPage
from pages.connections_page import ConnectionsPage


class TestConnections:
    """Test suite for connections page functionality."""
    
    def test_connections_page_loads_after_login(self, logged_in_driver, base_url):
        """Test that connections page loads after login."""
        connections_page = ConnectionsPage(logged_in_driver, base_url)
        
        # Should already be on connections page after login
        assert connections_page.is_on_connections_page(), "Should be on connections page"
        connections_page.wait_for_page_load()
    
    def test_connections_page_shows_title(self, logged_in_driver, base_url):
        """Test that connections page shows the correct title."""
        connections_page = ConnectionsPage(logged_in_driver, base_url)
        connections_page.wait_for_page_load()
        
        assert connections_page.is_element_present(connections_page.PAGE_TITLE), \
            "Page title should be present"
    
    def test_add_connection_button_present(self, logged_in_driver, base_url):
        """Test that Add Connection button is present."""
        connections_page = ConnectionsPage(logged_in_driver, base_url)
        connections_page.wait_for_page_load()
        connections_page.wait_for_connections_loaded()
        
        assert connections_page.is_element_present(connections_page.ADD_CONNECTION_BUTTON), \
            "Add Connection button should be present"
    
    def test_view_schema_button_present_for_connections(self, logged_in_driver, base_url):
        """Test that View Schema button is present for each connection."""
        connections_page = ConnectionsPage(logged_in_driver, base_url)
        connections_page.wait_for_page_load()
        connections_page.wait_for_connections_loaded()
        
        # If there are connections, View Schema should be available
        if not connections_page.has_no_connections():
            assert connections_page.is_element_present(connections_page.VIEW_SCHEMA_BUTTON), \
                "View Schema button should be present"
    
    def test_define_intent_button_present_for_connections(self, logged_in_driver, base_url):
        """Test that Define Intent button is present for each connection."""
        connections_page = ConnectionsPage(logged_in_driver, base_url)
        connections_page.wait_for_page_load()
        connections_page.wait_for_connections_loaded()
        
        # If there are connections, Define Intent should be available
        if not connections_page.has_no_connections():
            assert connections_page.is_element_present(connections_page.DEFINE_INTENT_BUTTON), \
                "Define Intent button should be present"
    
    def test_connection_cards_display_info(self, logged_in_driver, base_url):
        """Test that connection cards display connection information."""
        connections_page = ConnectionsPage(logged_in_driver, base_url)
        connections_page.wait_for_page_load()
        connections_page.wait_for_connections_loaded()
        
        if not connections_page.has_no_connections():
            names = connections_page.get_connection_names()
            assert len(names) > 0, "Should display connection names"

