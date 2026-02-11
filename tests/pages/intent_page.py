"""Intent Page Object."""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage


class IntentPage(BasePage):
    """Page object for the intent definition page."""
    
    # Locators
    PAGE_TITLE = (By.XPATH, "//h1[contains(text(), 'Define Analytical Intent')]")
    SCHEMA_DROPDOWN = (By.CSS_SELECTOR, "select.select.w-48")
    TABLE_DROPDOWN = (By.CSS_SELECTOR, "select.select.flex-1")
    TABLES_OF_INTEREST = (By.CSS_SELECTOR, ".rounded-lg.border-2")
    SELECTED_TABLE = (By.CSS_SELECTOR, ".bg-indigo-50")
    ERD_SECTION = (By.XPATH, "//*[contains(text(), 'Table Relationships')]")
    DETAILS_PANEL = (By.XPATH, "//*[contains(text(), 'Columns')]")
    BUSINESS_DOMAIN_INPUT = (By.CSS_SELECTOR, "input[placeholder*='E-commerce']")
    ANALYTICAL_GOAL_SELECT = (By.CSS_SELECTOR, "select")
    KEY_METRICS_INPUT = (By.CSS_SELECTOR, "input[placeholder*='revenue']")
    SUBMIT_BUTTON = (By.XPATH, "//button[contains(text(), 'Create Intent')]")
    LOADING_SPINNER = (By.CSS_SELECTOR, ".animate-spin")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".bg-red-50, .text-red-600")
    CONNECTION_ERROR = (By.XPATH, "//*[contains(text(), 'Connection Error')]")
    ADD_NOTES_BUTTON = (By.XPATH, "//button[contains(text(), 'Add notes')]")
    NOTES_TEXTAREA = (By.CSS_SELECTOR, "textarea.input")
    FACT_CHECKBOX = (By.XPATH, "//span[contains(text(), 'Fact')]/preceding-sibling::input")
    DIM_CHECKBOX = (By.XPATH, "//span[contains(text(), 'Dim')]/preceding-sibling::input")
    
    def navigate(self, connection_id: str):
        """Navigate to the intent page for a connection."""
        super().navigate(f"/intent/{connection_id}")
    
    def is_on_intent_page(self) -> bool:
        """Check if we're on the intent page."""
        return "/intent/" in self.get_current_url()
    
    def wait_for_page_load(self, timeout: int = 10):
        """Wait for the intent page to load."""
        self.wait_for_element(self.PAGE_TITLE, timeout)
    
    def has_connection_error(self) -> bool:
        """Check if there's a connection error."""
        return self.is_element_present(self.CONNECTION_ERROR)
    
    def get_schema_options(self) -> list:
        """Get available schema options."""
        options = self.find_elements((By.CSS_SELECTOR, "select.select.w-48 option"))
        return [opt.text for opt in options if opt.get_attribute("value")]
    
    def select_schema(self, schema_name: str):
        """Select a schema."""
        self.select_option_by_text(self.SCHEMA_DROPDOWN, schema_name)
    
    def get_table_options(self) -> list:
        """Get available table options."""
        options = self.find_elements((By.CSS_SELECTOR, "select.select.flex-1 option"))
        return [opt.text for opt in options if opt.get_attribute("value")]
    
    def add_table(self, table_name: str):
        """Add a table to tables of interest."""
        self.select_option_by_text(self.TABLE_DROPDOWN, table_name)
    
    def get_tables_of_interest_count(self) -> int:
        """Get count of tables of interest."""
        return len(self.find_elements(self.TABLES_OF_INTEREST))
    
    def click_table(self, table_name: str):
        """Click on a table in the tables of interest list."""
        xpath = f"//span[contains(@class, 'font-medium') and contains(text(), '{table_name}')]"
        self.click((By.XPATH, xpath))
    
    def is_erd_visible(self) -> bool:
        """Check if ERD section is visible."""
        return self.is_element_present(self.ERD_SECTION)
    
    def is_details_panel_visible(self) -> bool:
        """Check if details panel is visible."""
        return self.is_element_present(self.DETAILS_PANEL)
    
    def fill_business_domain(self, domain: str):
        """Fill in the business domain."""
        self.type_text(self.BUSINESS_DOMAIN_INPUT, domain)
    
    def fill_key_metrics(self, metrics: str):
        """Fill in key metrics."""
        self.type_text(self.KEY_METRICS_INPUT, metrics)
    
    def submit_intent(self):
        """Submit the intent form."""
        self.click(self.SUBMIT_BUTTON)
    
    def is_submit_enabled(self) -> bool:
        """Check if submit button is enabled."""
        button = self.find_element(self.SUBMIT_BUTTON)
        return button.is_enabled()
    
    def wait_for_schemas_loaded(self, timeout: int = 10):
        """Wait for schemas to load."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(self.get_schema_options()) > 0
            )
        except:
            pass

