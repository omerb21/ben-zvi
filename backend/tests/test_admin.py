"""
Tests for admin endpoints including database stats.
"""
import pytest


pytestmark = pytest.mark.anyio


class TestAdminStats:
    """Test admin statistics endpoint."""

    async def test_get_stats_empty_db(self, client):
        """Test stats endpoint on empty database."""
        response = await client.get("/api/v1/admin/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["totalClients"] == 0
        assert data["totalSnapshots"] == 0
        assert data["totalExistingProducts"] == 0
        assert data["totalNewProducts"] == 0
        assert data["totalFormInstances"] == 0
        assert data["totalBeneficiaries"] == 0
        assert data["totalSignatureRequests"] == 0
        assert data["pendingSignatureRequests"] == 0

    async def test_get_stats_with_data(self, client):
        """Test stats endpoint after creating some data."""
        # Create a client
        await client.post(
            "/api/v1/crm/clients",
            json={
                "idNumber": "123456789",
                "fullName": "טסט טסט",
                "firstName": "טסט",
            }
        )

        response = await client.get("/api/v1/admin/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["totalClients"] == 1
