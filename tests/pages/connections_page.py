"""Connections Page Object."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage


class ConnectionsPage(BasePage):
    """Page object for the connections page."""

    # Locators
    PAGE_TITLE = (By.XPATH, "//h1[contains(text(), 'Database Connections')]")
    ADD_CONNECTION_BUTTON = (By.XPATH, "//button[contains(text(), 'Add Connection')]")
    CONNECTION_CARDS = (By.CSS_SELECTOR, ".card, [data-testid='connection-card']")
    CONNECTION_NAME = (By.CSS_SELECTOR, ".font-semibold, .font-medium")
    VIEW_SCHEMA_BUTTON = (
        By.XPATH,
        "//a[contains(text(), 'View Schema')] | //button[contains(text(), 'View Schema')]",
    )
    DEFINE_INTENT_BUTTON = (
        By.XPATH,
        "//a[contains(text(), 'Create Intent')] | //button[contains(text(), 'Create Intent')]",
    )
    DELETE_BUTTON = (
        By.XPATH,
        "//button[contains(@class, 'text-red') or contains(text(), 'Delete')]",
    )
    TEST_CONNECTION_BUTTON = (By.XPATH, "//button[contains(text(), 'Test')]")
    LOADING_SPINNER = (By.CSS_SELECTOR, ".animate-spin, [data-testid='loading']")
    NO_CONNECTIONS_MESSAGE = (
        By.XPATH,
        "//*[contains(text(), 'No connections') or contains(text(), 'no connections')]",
    )

    def navigate(self):
        """Navigate to the connections page."""
        super().navigate("/connections")

    def is_on_connections_page(self) -> bool:
        """Check if we're on the connections page."""
        return "/connections" in self.get_current_url()

    def wait_for_page_load(self, timeout: int = 10):
        """Wait for the connections page to load."""
        self.wait_for_element(self.PAGE_TITLE, timeout)

    def get_connection_count(self) -> int:
        """Get the number of connection cards displayed."""
        cards = self.find_elements(self.CONNECTION_CARDS)
        return len(cards)

    def get_connection_names(self) -> list:
        """Get all connection names."""
        elements = self.find_elements(self.CONNECTION_NAME)
        return [el.text for el in elements if el.text]

    def click_add_connection(self):
        """Click the Add Connection button."""
        self.click(self.ADD_CONNECTION_BUTTON)

    def click_view_schema_for_connection(self, connection_name: str):
        """Click View Schema for a specific connection."""
        # Find the connection card containing the name
        xpath = f"//div[contains(@class, 'card')]//span[contains(text(), '{connection_name}')]/ancestor::div[contains(@class, 'card')]//a[contains(text(), 'View Schema')]"
        locator = (By.XPATH, xpath)
        self.click(locator)

    def click_define_intent_for_connection(self, connection_name: str):
        """Click Create Intent for a specific connection."""
        xpath = f"//div[contains(@class, 'card')]//span[contains(text(), '{connection_name}')]/ancestor::div[contains(@class, 'card')]//a[contains(text(), 'Create Intent')]"
        locator = (By.XPATH, xpath)
        self.click(locator)

    def is_connection_present(self, connection_name: str) -> bool:
        """Check if a connection with the given name exists."""
        return connection_name in self.get_connection_names()

    def has_no_connections(self) -> bool:
        """Check if there are no connections."""
        return (
            self.is_element_present(self.NO_CONNECTIONS_MESSAGE)
            or self.get_connection_count() == 0
        )

    def wait_for_connections_loaded(self, timeout: int = 10):
        """Wait for connections to be loaded (spinner gone)."""
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(self.LOADING_SPINNER)
            )
            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located(self.LOADING_SPINNER)
            )
        except:
            pass  # Spinner might not appear if data loads quickly
