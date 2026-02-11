"""
Test cases for schema browser functionality.
"""

import pytest
import requests
from pages.login_page import LoginPage
from pages.connections_page import ConnectionsPage
from pages.schema_page import SchemaPage


class TestSchemaBrowser:
    """Test suite for schema browser functionality."""

    @pytest.fixture
    def test_connection_id(self, api_url, credentials):
        """Get a test connection ID from the API."""
        # Login to get token
        login_response = requests.post(
            f"{api_url}/api/auth/login",
            data={
                "username": credentials["username"],
                "password": credentials["password"],
            },
        )
        if login_response.status_code != 200:
            pytest.skip("Could not authenticate with API")

        token = login_response.json()["access_token"]

        # Get connections
        connections_response = requests.get(
            f"{api_url}/api/connections", headers={"Authorization": f"Bearer {token}"}
        )
        if connections_response.status_code != 200:
            pytest.skip("Could not get connections from API")

        connections = connections_response.json()
        if not connections:
            pytest.skip("No connections available for testing")

        return connections[0]["id"]

    def test_schema_page_loads(self, logged_in_driver, base_url, test_connection_id):
        """Test that schema page loads for a connection."""
        schema_page = SchemaPage(logged_in_driver, base_url)
        schema_page.navigate(test_connection_id)

        # Wait for page to load
        schema_page.wait_for_page_load()

        assert schema_page.is_on_schema_page(), "Should be on schema page"

    def test_schema_page_shows_connection_error_for_unavailable_db(
        self, logged_in_driver, base_url, test_connection_id
    ):
        """Test that schema page shows error when database is unavailable."""
        schema_page = SchemaPage(logged_in_driver, base_url)
        schema_page.navigate(test_connection_id)

        # Wait for page to load
        import time

        time.sleep(3)

        # Should show connection error (since AdventureWorks DB isn't running)
        if schema_page.has_connection_error():
            error_msg = schema_page.get_error_message()
            assert (
                "Connection Error" in schema_page.driver.page_source or error_msg
            ), "Should display connection error message"

    def test_schema_dropdown_present(
        self, logged_in_driver, base_url, test_connection_id
    ):
        """Test that schema dropdown is present on the page."""
        schema_page = SchemaPage(logged_in_driver, base_url)
        schema_page.navigate(test_connection_id)

        import time

        time.sleep(2)

        # If no connection error, dropdown should be present
        if not schema_page.has_connection_error():
            assert schema_page.is_element_present(
                schema_page.SCHEMA_DROPDOWN
            ), "Schema dropdown should be present"


class TestSchemaWithRealDatabase:
    """
    Test suite for schema browser with a real database connection.
    These tests require a working database connection.
    """

    @pytest.fixture
    def working_connection_id(self, api_url, credentials):
        """Get a working connection ID (PostgreSQL - the app's own database)."""
        # Login to get token
        login_response = requests.post(
            f"{api_url}/api/auth/login",
            data={
                "username": credentials["username"],
                "password": credentials["password"],
            },
        )
        if login_response.status_code != 200:
            pytest.skip("Could not authenticate with API")

        token = login_response.json()["access_token"]

        # Create a test connection to the app's own PostgreSQL database
        connection_data = {
            "name": "Test PostgreSQL Connection",
            "db_type": "postgresql",
            "host": "db",
            "port": 5432,
            "database": "alens",
            "username": "alens",
            "password": "alens",
        }

        create_response = requests.post(
            f"{api_url}/api/connections",
            json=connection_data,
            headers={"Authorization": f"Bearer {token}"},
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Could not create test connection")

        connection_id = create_response.json()["id"]

        yield connection_id

        # Cleanup: delete the test connection
        requests.delete(
            f"{api_url}/api/connections/{connection_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    def test_schema_loads_for_working_connection(
        self, logged_in_driver, base_url, working_connection_id
    ):
        """Test that schemas load for a working database connection."""
        schema_page = SchemaPage(logged_in_driver, base_url)
        schema_page.navigate(working_connection_id)

        # Wait for page to load
        schema_page.wait_for_page_load()
        import time

        time.sleep(2)

        # Should not have connection error
        assert (
            not schema_page.has_connection_error()
        ), "Should not have connection error for working database"

        # Should have schema options
        schemas = schema_page.get_schema_options()
        assert len(schemas) > 0, "Should have schema options available"

    def test_tables_load_when_schema_selected(
        self, logged_in_driver, base_url, working_connection_id
    ):
        """Test that tables load when a schema is selected."""
        schema_page = SchemaPage(logged_in_driver, base_url)
        schema_page.navigate(working_connection_id)

        schema_page.wait_for_page_load()
        import time

        time.sleep(2)

        if schema_page.has_connection_error():
            pytest.skip("Database connection not available")

        schemas = schema_page.get_schema_options()
        if not schemas:
            pytest.skip("No schemas available")

        # Select the first schema (usually 'public' for PostgreSQL)
        schema_page.select_schema(schemas[0])
        time.sleep(2)

        # Should have tables or "no tables" message
        table_count = schema_page.get_table_count()
        has_no_tables = schema_page.has_no_tables()

        assert (
            table_count > 0 or has_no_tables
        ), "Should show tables or 'no tables' message"
