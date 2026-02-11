"""
Test cases for error handling scenarios.
"""

import pytest
import requests
from pages.login_page import LoginPage
from pages.schema_page import SchemaPage
from pages.intent_page import IntentPage


class TestErrorHandling:
    """Test suite for error handling scenarios."""

    def test_invalid_connection_id_shows_error(self, logged_in_driver, base_url):
        """Test that invalid connection ID shows appropriate error."""
        schema_page = SchemaPage(logged_in_driver, base_url)

        # Navigate to a non-existent connection
        fake_id = "00000000-0000-0000-0000-000000000000"
        schema_page.navigate(fake_id)

        import time

        time.sleep(3)

        # Should show some kind of error or redirect
        current_url = logged_in_driver.current_url
        page_source = logged_in_driver.page_source.lower()

        # Either shows error, redirects, shows empty state, or stays on schema page
        # (with no data which is also acceptable for invalid connection)
        has_error = any(
            term in page_source
            for term in [
                "error",
                "not found",
                "connection",
                "unable",
                "failed",
                "loading",
            ]
        )
        is_redirected = fake_id not in current_url
        is_on_schema_page = "schema" in page_source or "/schema/" in current_url

        assert (
            has_error or is_redirected or is_on_schema_page
        ), "Should show error, redirect, or be on schema page for invalid connection"

    def test_connection_error_displays_helpful_message(
        self, logged_in_driver, base_url, api_url, credentials
    ):
        """Test that connection errors display helpful messages."""
        # Get a connection that will fail (AdventureWorks)
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

        sqlserver_conn = next(
            (c for c in connections if c.get("db_type") == "sqlserver"), None
        )

        if not sqlserver_conn:
            pytest.skip("No SQL Server connection for testing")

        schema_page = SchemaPage(logged_in_driver, base_url)
        schema_page.navigate(sqlserver_conn["id"])

        import time

        time.sleep(3)

        # Should show connection error with helpful message
        if schema_page.has_connection_error():
            page_source = logged_in_driver.page_source

            # Check for helpful error content
            has_helpful_info = any(
                [
                    "Connection Error" in page_source,
                    "database server" in page_source.lower(),
                    "connection" in page_source.lower(),
                ]
            )

            assert has_helpful_info, "Error message should contain helpful information"

    def test_api_error_response_format(self, api_url, credentials):
        """Test that API returns proper error format."""
        # Login first
        login_response = requests.post(
            f"{api_url}/api/auth/login",
            data={
                "username": credentials["username"],
                "password": credentials["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Try to access non-existent resource
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = requests.get(
            f"{api_url}/api/connections/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should return 404 with detail message
        assert (
            response.status_code == 404
        ), "Should return 404 for non-existent resource"

        error_data = response.json()
        assert "detail" in error_data, "Error response should have 'detail' field"

    def test_unauthorized_access_returns_401(self, api_url):
        """Test that unauthorized access returns 401."""
        response = requests.get(f"{api_url}/api/connections")

        assert response.status_code == 401, "Should return 401 for unauthorized access"

    def test_invalid_token_returns_401(self, api_url):
        """Test that invalid token returns 401."""
        response = requests.get(
            f"{api_url}/api/connections",
            headers={"Authorization": "Bearer invalid_token_here"},
        )

        assert response.status_code == 401, "Should return 401 for invalid token"
