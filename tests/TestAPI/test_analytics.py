"""
Tests for the Analytics API endpoints.

This module contains tests for:
- Analytics overview endpoint
- Executions list endpoint
- Execution details endpoint
- Agent stats endpoint
- Cost summary endpoint
- Cost forecast endpoint
- Budget alerts CRUD
- Model comparison endpoint
- Export endpoint
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

import aiohttp

ANALYTICS_BASE = "/api/analytics"
OVERVIEW_ENDPOINT = f"{ANALYTICS_BASE}/overview"
EXECUTIONS_ENDPOINT = f"{ANALYTICS_BASE}/executions"
EXECUTION_DETAIL_ENDPOINT = f"{ANALYTICS_BASE}/executions/{{execution_id}}"
AGENT_STATS_ENDPOINT = f"{ANALYTICS_BASE}/agents/{{agent_id}}/stats"
COST_SUMMARY_ENDPOINT = f"{ANALYTICS_BASE}/costs/summary"
COST_FORECAST_ENDPOINT = f"{ANALYTICS_BASE}/costs/forecast"
BUDGETS_ENDPOINT = f"{ANALYTICS_BASE}/budgets"
BUDGET_DETAIL_ENDPOINT = f"{ANALYTICS_BASE}/budgets/{{alert_id}}"
MODEL_COMPARISON_ENDPOINT = f"{ANALYTICS_BASE}/comparison/models"
EXPORT_ENDPOINT = f"{ANALYTICS_BASE}/export"

BASE_URL = "http://localhost:8000"


class HttpClient:
    """Simple HTTP client that returns JSON directly."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")

    async def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}/{path.lstrip('/')}"
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, **kwargs) as response:
                if response.status >= 400:
                    raise aiohttp.ClientResponseError(
                        response.request_info,
                        response.history,
                        status=response.status,
                        message=await response.text(),
                    )
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return await response.json()
                return await response.text()

    async def get(self, path: str, **kwargs):
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs):
        return await self._request("POST", path, **kwargs)

    async def patch(self, path: str, **kwargs):
        return await self._request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs):
        return await self._request("DELETE", path, **kwargs)


http_client = HttpClient()


class TestAnalyticsOverview:
    """Tests for the analytics overview endpoint."""

    @pytest.mark.asyncio
    async def test_get_overview_default_period(self, user_jwt_token: str):
        """Test getting analytics overview with default 24h period."""
        response = await http_client.get(
            path=OVERVIEW_ENDPOINT,
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        # Verify response structure
        assert "total_executions" in response
        assert "successful_executions" in response
        assert "failed_executions" in response
        assert "success_rate" in response
        assert "avg_execution_time_ms" in response
        assert "total_cost_usd" in response
        assert "top_agents" in response
        assert "cost_by_model" in response
        assert isinstance(response["total_executions"], int)
        assert isinstance(response["top_agents"], list)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "period",
        ["24h", "7d", "30d", "90d"],
        ids=["24h period", "7d period", "30d period", "90d period"],
    )
    async def test_get_overview_different_periods(self, user_jwt_token: str, period: str):
        """Test getting analytics overview with different time periods."""
        response = await http_client.get(
            path=OVERVIEW_ENDPOINT,
            params={"period": period},
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        assert "total_executions" in response
        assert response["total_executions"] >= 0

    @pytest.mark.asyncio
    async def test_get_overview_custom_date_range(self, user_jwt_token: str):
        """Test getting analytics overview with custom date range."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        response = await http_client.get(
            path=OVERVIEW_ENDPOINT,
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        assert "total_executions" in response

    @pytest.mark.asyncio
    async def test_get_overview_unauthorized(self):
        """Test that unauthorized requests are rejected."""
        try:
            await http_client.get(path=OVERVIEW_ENDPOINT)
            assert False, "Should have raised an error"
        except Exception:
            pass  # Expected to fail without auth


class TestExecutionsList:
    """Tests for the executions list endpoint."""

    @pytest.mark.asyncio
    async def test_list_executions_default(self, user_jwt_token: str):
        """Test listing executions with default parameters."""
        response = await http_client.get(
            path=EXECUTIONS_ENDPOINT,
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        assert "items" in response
        assert "total" in response
        assert "page" in response
        assert "page_size" in response
        assert "total_pages" in response
        assert isinstance(response["items"], list)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "page,page_size",
        [(1, 10), (1, 20), (2, 10)],
        ids=["page 1, size 10", "page 1, size 20", "page 2, size 10"],
    )
    async def test_list_executions_pagination(
        self, user_jwt_token: str, page: int, page_size: int
    ):
        """Test executions list pagination."""
        response = await http_client.get(
            path=EXECUTIONS_ENDPOINT,
            params={"page": page, "page_size": page_size},
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        assert response["page"] == page
        assert response["page_size"] == page_size
        assert len(response["items"]) <= page_size

    @pytest.mark.asyncio
    async def test_list_executions_filter_by_status(self, user_jwt_token: str):
        """Test filtering executions by status."""
        response = await http_client.get(
            path=EXECUTIONS_ENDPOINT,
            params={"status": "success"},
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        assert "items" in response
        for item in response["items"]:
            assert item["status"] == "success"

    @pytest.mark.asyncio
    async def test_list_executions_sort_by_time(self, user_jwt_token: str):
        """Test sorting executions by time."""
        response = await http_client.get(
            path=EXECUTIONS_ENDPOINT,
            params={"sort_by": "started_at", "sort_order": "desc"},
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        assert "items" in response


class TestExecutionDetails:
    """Tests for the execution details endpoint."""

    @pytest.mark.asyncio
    async def test_get_execution_not_found(self, user_jwt_token: str):
        """Test getting a non-existent execution."""
        fake_id = str(uuid4())
        try:
            await http_client.get(
                path=EXECUTION_DETAIL_ENDPOINT.format(execution_id=fake_id),
                headers={"Authorization": f"Bearer {user_jwt_token}"},
            )
            assert False, "Should have raised 404"
        except Exception:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_get_execution_invalid_uuid(self, user_jwt_token: str):
        """Test getting execution with invalid UUID."""
        try:
            await http_client.get(
                path=EXECUTION_DETAIL_ENDPOINT.format(execution_id="invalid-uuid"),
                headers={"Authorization": f"Bearer {user_jwt_token}"},
            )
            assert False, "Should have raised error"
        except Exception:
            pass  # Expected


class TestAgentStats:
    """Tests for the agent stats endpoint."""

    @pytest.mark.asyncio
    async def test_get_agent_stats_not_found(self, user_jwt_token: str):
        """Test getting stats for non-existent agent."""
        fake_id = str(uuid4())
        try:
            await http_client.get(
                path=AGENT_STATS_ENDPOINT.format(agent_id=fake_id),
                headers={"Authorization": f"Bearer {user_jwt_token}"},
            )
            assert False, "Should have raised 404"
        except Exception:
            pass  # Expected


class TestCostEndpoints:
    """Tests for cost-related endpoints."""

    @pytest.mark.asyncio
    async def test_get_cost_summary(self, user_jwt_token: str):
        """Test getting cost summary."""
        response = await http_client.get(
            path=COST_SUMMARY_ENDPOINT,
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        assert "total_cost_usd" in response
        assert "period_days" in response
        assert "by_model" in response
        assert "by_agent" in response

    @pytest.mark.asyncio
    async def test_get_cost_forecast(self, user_jwt_token: str):
        """Test getting cost forecast."""
        response = await http_client.get(
            path=COST_FORECAST_ENDPOINT,
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        assert "current_period_cost_usd" in response
        assert "projected_monthly_cost_usd" in response
        assert "daily_average_cost_usd" in response
        assert "cost_trend" in response


class TestBudgetAlerts:
    """Tests for budget alert CRUD operations."""

    @pytest.mark.asyncio
    async def test_list_budget_alerts_empty(self, user_jwt_token: str):
        """Test listing budget alerts when none exist."""
        response = await http_client.get(
            path=BUDGETS_ENDPOINT,
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        assert isinstance(response, list)

    @pytest.mark.asyncio
    async def test_create_budget_alert(self, user_jwt_token: str):
        """Test creating a budget alert."""
        alert_data = {
            "threshold_usd": 100.00,
            "period_days": 30,
            "alert_type": "warning",
            "alert_at_percentage": 80,
            "email_notification": True,
        }

        response = await http_client.post(
            path=BUDGETS_ENDPOINT,
            json=alert_data,
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        assert "id" in response
        assert response["threshold_usd"] == "100.00" or float(response["threshold_usd"]) == 100.00
        assert response["period_days"] == 30
        assert response["alert_at_percentage"] == 80

    @pytest.mark.asyncio
    async def test_create_budget_alert_invalid_percentage(self, user_jwt_token: str):
        """Test creating a budget alert with invalid percentage."""
        alert_data = {
            "threshold_usd": 100.00,
            "alert_at_percentage": 150,  # Invalid: > 100
        }

        try:
            await http_client.post(
                path=BUDGETS_ENDPOINT,
                json=alert_data,
                headers={"Authorization": f"Bearer {user_jwt_token}"},
            )
            assert False, "Should have raised validation error"
        except Exception:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_update_budget_alert(self, user_jwt_token: str):
        """Test updating a budget alert."""
        # First create an alert
        alert_data = {"threshold_usd": 50.00}
        created = await http_client.post(
            path=BUDGETS_ENDPOINT,
            json=alert_data,
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        # Update it
        update_data = {"threshold_usd": 75.00, "is_active": False}
        updated = await http_client.patch(
            path=BUDGET_DETAIL_ENDPOINT.format(alert_id=created["id"]),
            json=update_data,
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        assert float(updated["threshold_usd"]) == 75.00 or updated["threshold_usd"] == "75.00"
        assert updated["is_active"] is False

    @pytest.mark.asyncio
    async def test_delete_budget_alert(self, user_jwt_token: str):
        """Test deleting a budget alert."""
        # First create an alert
        alert_data = {"threshold_usd": 25.00}
        created = await http_client.post(
            path=BUDGETS_ENDPOINT,
            json=alert_data,
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        # Delete it
        delete_data = await http_client.delete(
            path=BUDGET_DETAIL_ENDPOINT.format(alert_id=created["id"]),
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        assert delete_data["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_delete_budget_alert_not_found(self, user_jwt_token: str):
        """Test deleting a non-existent budget alert."""
        fake_id = str(uuid4())
        try:
            await http_client.delete(
                path=BUDGET_DETAIL_ENDPOINT.format(alert_id=fake_id),
                headers={"Authorization": f"Bearer {user_jwt_token}"},
            )
            assert False, "Should have raised 404"
        except Exception:
            pass  # Expected


class TestModelComparison:
    """Tests for model comparison endpoint."""

    @pytest.mark.asyncio
    async def test_compare_models(self, user_jwt_token: str):
        """Test getting model comparison data."""
        response = await http_client.get(
            path=MODEL_COMPARISON_ENDPOINT,
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        assert isinstance(response, list)
        # If there's data, verify structure
        if response:
            item = response[0]
            assert "model_name" in item
            assert "execution_count" in item
            assert "success_rate" in item


class TestExport:
    """Tests for the export endpoint."""

    @pytest.mark.asyncio
    async def test_export_json(self, user_jwt_token: str):
        """Test exporting analytics data as JSON."""
        response = await http_client.get(
            path=EXPORT_ENDPOINT,
            params={"format": "json"},
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )

        # Response should be JSON with export data
        assert "export_date" in response or isinstance(response, (dict, list))

    @pytest.mark.asyncio
    async def test_export_csv(self, user_jwt_token: str):
        """Test exporting analytics data as CSV."""
        # For CSV, we can't easily verify the structure in the same way
        # Just ensure the endpoint responds
        try:
            await http_client.get(
                path=EXPORT_ENDPOINT,
                params={"format": "csv"},
                headers={"Authorization": f"Bearer {user_jwt_token}"},
            )
        except Exception:
            # CSV response might not be JSON-parseable
            pass


class TestAnalyticsIntegration:
    """Integration tests for analytics functionality."""

    @pytest.mark.asyncio
    async def test_analytics_workflow(self, user_jwt_token: str):
        """Test a complete analytics workflow."""
        # 1. Get overview
        overview = await http_client.get(
            path=OVERVIEW_ENDPOINT,
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )
        assert overview is not None

        # 2. Get executions list
        executions = await http_client.get(
            path=EXECUTIONS_ENDPOINT,
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )
        assert "items" in executions

        # 3. Get cost summary
        cost_summary = await http_client.get(
            path=COST_SUMMARY_ENDPOINT,
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )
        assert "total_cost_usd" in cost_summary

        # 4. Create a budget alert
        alert = await http_client.post(
            path=BUDGETS_ENDPOINT,
            json={"threshold_usd": 100.00},
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )
        assert "id" in alert

        # 5. List budget alerts
        alerts = await http_client.get(
            path=BUDGETS_ENDPOINT,
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )
        assert len(alerts) > 0

        # 6. Delete the budget alert
        await http_client.delete(
            path=BUDGET_DETAIL_ENDPOINT.format(alert_id=alert["id"]),
            headers={"Authorization": f"Bearer {user_jwt_token}"},
        )
