"""Schema Page Object."""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage


class SchemaPage(BasePage):
    """Page object for the schema browser page."""
    
    # Locators
    PAGE_TITLE = (By.XPATH, "//h1[contains(text(), 'Schema Browser')]")
    SCHEMA_DROPDOWN = (By.CSS_SELECTOR, "select.select")
    SCHEMA_OPTIONS = (By.CSS_SELECTOR, "select.select option")
    TABLE_CARDS = (By.CSS_SELECTOR, ".card")
    TABLE_NAME = (By.CSS_SELECTOR, ".font-medium")
    EXPAND_TABLE_BUTTON = (By.CSS_SELECTOR, "button.w-full")
    COLUMN_ROWS = (By.CSS_SELECTOR, "tbody tr")
    LOADING_SPINNER = (By.CSS_SELECTOR, ".animate-spin")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".bg-red-50, .text-red-600, [role='alert']")
    CONNECTION_ERROR_TITLE = (By.XPATH, "//*[contains(text(), 'Connection Error')]")
    NO_TABLES_MESSAGE = (By.XPATH, "//*[contains(text(), 'No tables found')]")
    FK_SECTION = (By.XPATH, "//*[contains(text(), 'Foreign Keys')]")
    
    def navigate(self, connection_id: str):
        """Navigate to the schema page for a connection."""
        super().navigate(f"/schema/{connection_id}")
    
    def is_on_schema_page(self) -> bool:
        """Check if we're on the schema page."""
        return "/schema/" in self.get_current_url()
    
    def wait_for_page_load(self, timeout: int = 10):
        """Wait for the schema page to load."""
        self.wait_for_element(self.PAGE_TITLE, timeout)
    
    def has_connection_error(self) -> bool:
        """Check if there's a connection error displayed."""
        return self.is_element_present(self.CONNECTION_ERROR_TITLE) or self.is_element_present(self.ERROR_MESSAGE)
    
    def get_error_message(self) -> str:
        """Get the error message text."""
        try:
            error_elements = self.find_elements(self.ERROR_MESSAGE)
            return " ".join([el.text for el in error_elements])
        except:
            return ""
    
    def get_schema_options(self) -> list:
        """Get all available schema options."""
        options = self.find_elements(self.SCHEMA_OPTIONS)
        return [opt.text for opt in options if opt.get_attribute("value")]
    
    def select_schema(self, schema_name: str):
        """Select a schema from the dropdown."""
        self.select_option_by_text(self.SCHEMA_DROPDOWN, schema_name)
    
    def get_table_count(self) -> int:
        """Get the number of tables displayed."""
        tables = self.find_elements(self.TABLE_CARDS)
        # Filter out non-table cards
        return len([t for t in tables if t.find_elements(By.CSS_SELECTOR, ".font-medium")])
    
    def get_table_names(self) -> list:
        """Get all table names."""
        elements = self.find_elements(self.TABLE_NAME)
        return [el.text for el in elements if el.text]
    
    def expand_table(self, table_name: str):
        """Expand a table to show its columns."""
        xpath = f"//span[contains(@class, 'font-medium') and contains(text(), '{table_name}')]/ancestor::button"
        locator = (By.XPATH, xpath)
        self.click(locator)
    
    def get_column_count_for_table(self, table_name: str) -> int:
        """Get the number of columns for an expanded table."""
        # First expand the table
        self.expand_table(table_name)
        # Wait for columns to appear
        import time
        time.sleep(0.5)
        rows = self.find_elements(self.COLUMN_ROWS)
        return len(rows)
    
    def is_table_expanded(self, table_name: str) -> bool:
        """Check if a table is expanded."""
        xpath = f"//span[contains(@class, 'font-medium') and contains(text(), '{table_name}')]/ancestor::div[contains(@class, 'card')]//tbody"
        return self.is_element_present((By.XPATH, xpath))
    
    def wait_for_tables_loaded(self, timeout: int = 10):
        """Wait for tables to be loaded."""
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(self.LOADING_SPINNER)
            )
            WebDriverWait(self.driver, timeout).until_not(
                EC.presence_of_element_located(self.LOADING_SPINNER)
            )
        except:
            pass
    
    def has_no_tables(self) -> bool:
        """Check if there are no tables."""
        return self.is_element_present(self.NO_TABLES_MESSAGE)

