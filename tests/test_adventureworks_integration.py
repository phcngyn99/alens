"""
Integration tests for AdventureWorks SQL Server database.
These tests require the sqlserver-test container to be running with AdventureWorks database.
"""

import os
import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from pages.connections_page import ConnectionsPage
from pages.schema_page import SchemaPage


class TestAdventureWorksIntegration:
    """Tests that verify AdventureWorks database integration works correctly."""

    @pytest.fixture
    def api_token(self, api_url, credentials):
        """Get an API token for making authenticated requests."""
        response = requests.post(
            f"{api_url}/api/auth/login",
            data={
                "username": credentials["username"],
                "password": credentials["password"],
            },
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]

    @pytest.fixture
    def adventureworks_connection(self, api_url, api_token):
        """Get the AdventureWorks connection from the API."""
        response = requests.get(
            f"{api_url}/api/connections",
            headers={"Authorization": f"Bearer {api_token}"},
        )
        assert response.status_code == 200
        connections = response.json()

        # Find the AdventureWorks connection
        aw_conn = next(
            (c for c in connections if "AdventureWorks" in c.get("name", "")), None
        )
        return aw_conn

    def test_adventureworks_connection_exists(self, adventureworks_connection):
        """Test that AdventureWorks connection is present in the system."""
        assert (
            adventureworks_connection is not None
        ), "AdventureWorks connection should exist"
        assert adventureworks_connection["db_type"] == "sqlserver"
        assert adventureworks_connection["database_name"] == "AdventureWorks2022"

    def test_adventureworks_schemas_accessible(
        self, api_url, api_token, adventureworks_connection
    ):
        """Test that AdventureWorks schemas can be retrieved via API."""
        if not adventureworks_connection:
            pytest.skip("AdventureWorks connection not found")

        conn_id = adventureworks_connection["id"]
        response = requests.get(
            f"{api_url}/api/introspect/{conn_id}/schemas",
            headers={"Authorization": f"Bearer {api_token}"},
        )

        # If SQL Server is not running, we'll get a 503
        if response.status_code == 503:
            pytest.skip("SQL Server container not available")

        assert response.status_code == 200, f"Failed to get schemas: {response.text}"
        schemas = response.json()

        # Verify expected schemas are present (API returns list of strings)
        expected_schemas = [
            "HumanResources",
            "Person",
            "Production",
            "Purchasing",
            "Sales",
        ]

        for expected in expected_schemas:
            assert (
                expected in schemas
            ), f"Expected schema '{expected}' not found in {schemas}"

    def test_adventureworks_tables_accessible(
        self, api_url, api_token, adventureworks_connection
    ):
        """Test that AdventureWorks tables can be retrieved for each schema."""
        if not adventureworks_connection:
            pytest.skip("AdventureWorks connection not found")

        conn_id = adventureworks_connection["id"]

        # First get schemas
        schemas_response = requests.get(
            f"{api_url}/api/introspect/{conn_id}/schemas",
            headers={"Authorization": f"Bearer {api_token}"},
        )

        if schemas_response.status_code == 503:
            pytest.skip("SQL Server container not available")

        assert schemas_response.status_code == 200
        schemas = schemas_response.json()  # List of schema name strings

        # Check that each schema has tables
        for schema_name in schemas[:3]:  # Test first 3 schemas to save time
            tables_response = requests.get(
                f"{api_url}/api/introspect/{conn_id}/schemas/{schema_name}/tables",
                headers={"Authorization": f"Bearer {api_token}"},
            )
            assert (
                tables_response.status_code == 200
            ), f"Failed to get tables for {schema_name}"
            tables = tables_response.json()  # List of table name strings
            assert len(tables) > 0, f"Schema {schema_name} should have tables"

    def test_schema_browser_displays_adventureworks_schemas(
        self, logged_in_driver, base_url, adventureworks_connection
    ):
        """Test that the Schema Browser UI correctly displays AdventureWorks schemas."""
        if not adventureworks_connection:
            pytest.skip("AdventureWorks connection not found")

        schema_page = SchemaPage(logged_in_driver, base_url)
        schema_page.navigate(adventureworks_connection["id"])

        # Wait for page to load
        import time

        time.sleep(3)

        # Check if there's a connection error (SQL Server not running)
        if schema_page.has_connection_error():
            pytest.skip(
                "SQL Server container not available - connection error displayed"
            )

        # Verify schema dropdown is present and has options
        try:
            wait = WebDriverWait(logged_in_driver, 10)
            schema_select = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "select"))
            )

            # Get the options
            select = Select(schema_select)
            options = [opt.text for opt in select.options if opt.text]

            # Should have the expected schemas
            expected = ["HumanResources", "Person", "Production", "Purchasing", "Sales"]
            for schema in expected:
                assert any(
                    schema in opt for opt in options
                ), f"Schema {schema} not in dropdown"

        except Exception as e:
            pytest.fail(f"Failed to verify schema dropdown: {str(e)}")

    def test_table_details_accessible_for_adventureworks(
        self, api_url, api_token, adventureworks_connection
    ):
        """Test that table column details can be retrieved for AdventureWorks tables."""
        if not adventureworks_connection:
            pytest.skip("AdventureWorks connection not found")

        conn_id = adventureworks_connection["id"]

        # Get tables from Person schema
        tables_response = requests.get(
            f"{api_url}/api/introspect/{conn_id}/schemas/Person/tables",
            headers={"Authorization": f"Bearer {api_token}"},
        )

        if tables_response.status_code == 503:
            pytest.skip("SQL Server container not available")

        assert tables_response.status_code == 200
        tables = tables_response.json()  # List of table name strings

        # Get table details (including columns) for a table
        if tables:
            table_name = tables[0]  # tables is a list of strings
            # The API endpoint returns table details including columns
            table_response = requests.get(
                f"{api_url}/api/introspect/{conn_id}/schemas/Person/tables/{table_name}",
                headers={"Authorization": f"Bearer {api_token}"},
            )
            assert table_response.status_code == 200
            table_data = table_response.json()
            # Table response includes columns
            assert (
                "columns" in table_data
            ), f"Table {table_name} response should include columns"
            assert (
                len(table_data["columns"]) > 0
            ), f"Table {table_name} should have columns"
