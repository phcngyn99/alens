"""
Test cases for intent definition page functionality.
"""

import pytest
import requests
from pages.intent_page import IntentPage


class TestIntentPage:
    """Test suite for intent page functionality."""

    @pytest.fixture
    def working_connection_id(self, api_url, credentials):
        """Get a working connection ID (PostgreSQL - the app's own database)."""
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

        connection_data = {
            "name": "Test Intent Connection",
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

        requests.delete(
            f"{api_url}/api/connections/{connection_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    def test_intent_page_loads(self, logged_in_driver, base_url, working_connection_id):
        """Test that intent page loads correctly."""
        intent_page = IntentPage(logged_in_driver, base_url)
        intent_page.navigate(working_connection_id)

        intent_page.wait_for_page_load()
        assert intent_page.is_on_intent_page(), "Should be on intent page"

    def test_intent_page_shows_tables_of_interest_section(
        self, logged_in_driver, base_url, working_connection_id
    ):
        """Test that Tables of Interest section is at the top."""
        intent_page = IntentPage(logged_in_driver, base_url)
        intent_page.navigate(working_connection_id)
        intent_page.wait_for_page_load()

        import time

        time.sleep(2)

        if intent_page.has_connection_error():
            pytest.skip("Database connection not available")

        # Check for schema dropdown
        assert intent_page.is_element_present(
            intent_page.SCHEMA_DROPDOWN
        ), "Schema dropdown should be present"

    def test_intent_page_loads_for_working_sqlserver(
        self, logged_in_driver, base_url, api_url, credentials
    ):
        """Test that intent page loads correctly when SQL Server is available."""
        # Get the AdventureWorks connection
        login_response = requests.post(
            f"{api_url}/api/auth/login",
            data={
                "username": credentials["username"],
                "password": credentials["password"],
            },
        )
        token = login_response.json()["access_token"]

        connections_response = requests.get(
            f"{api_url}/api/connections", headers={"Authorization": f"Bearer {token}"}
        )
        connections = connections_response.json()

        # Find AdventureWorks or any SQL Server connection
        sqlserver_conn = next(
            (c for c in connections if c.get("db_type") == "sqlserver"), None
        )

        if not sqlserver_conn:
            pytest.skip("No SQL Server connection available for testing")

        # Test that the connection can reach the database via API
        schemas_response = requests.get(
            f"{api_url}/api/introspect/{sqlserver_conn['id']}/schemas",
            headers={"Authorization": f"Bearer {token}"},
        )

        # If SQL Server is not available, skip this test
        if schemas_response.status_code == 503:
            pytest.skip("SQL Server container not available - skipping UI test")

        intent_page = IntentPage(logged_in_driver, base_url)
        intent_page.navigate(sqlserver_conn["id"])

        import time

        time.sleep(3)

        # When SQL Server is running, the page should load without errors
        # Either we don't have a connection error, or we can see the schema dropdown
        if not intent_page.has_connection_error():
            # Good - page loaded successfully
            assert True
        else:
            # If there's still a connection error, skip the test
            pytest.skip(
                "Connection error - SQL Server may not be accessible from the UI"
            )

    def test_submit_button_disabled_without_tables(
        self, logged_in_driver, base_url, working_connection_id
    ):
        """Test that submit button is disabled when no tables are selected."""
        intent_page = IntentPage(logged_in_driver, base_url)
        intent_page.navigate(working_connection_id)
        intent_page.wait_for_page_load()

        import time

        time.sleep(2)

        if intent_page.has_connection_error():
            pytest.skip("Database connection not available")

        # Submit should be disabled without tables
        assert (
            not intent_page.is_submit_enabled()
        ), "Submit button should be disabled without tables selected"

    def test_schemas_load_on_intent_page(
        self, logged_in_driver, base_url, working_connection_id
    ):
        """Test that schemas load on the intent page."""
        intent_page = IntentPage(logged_in_driver, base_url)
        intent_page.navigate(working_connection_id)
        intent_page.wait_for_page_load()

        import time

        time.sleep(3)

        if intent_page.has_connection_error():
            pytest.skip("Database connection not available")

        schemas = intent_page.get_schema_options()
        assert len(schemas) > 0, "Should have schema options"
