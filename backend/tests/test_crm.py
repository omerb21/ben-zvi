"""
Tests for CRM core flows: client CRUD and beneficiaries.
"""
import pytest


class TestClientCRUD:
    """Test client create, read, update operations."""

    def test_create_client(self, client):
        """Test creating a new client."""
        response = client.post(
            "/api/v1/crm/clients",
            json={
                "idNumber": "123456789",
                "fullName": "ישראל ישראלי",
                "firstName": "ישראל",
                "lastName": "ישראלי",
                "email": "test@example.com",
                "phone": "0501234567",
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["idNumber"] == "123456789"
        assert data["firstName"] == "ישראל"
        assert data["lastName"] == "ישראלי"
        assert "id" in data

    def test_get_client(self, client):
        """Test getting a client by ID."""
        # First create a client
        create_response = client.post(
            "/api/v1/crm/clients",
            json={
                "idNumber": "987654321",
                "fullName": "דוד כהן",
                "firstName": "דוד",
                "lastName": "כהן",
            }
        )
        assert create_response.status_code == 201
        client_id = create_response.json()["id"]

        # Then get it
        get_response = client.get(f"/api/v1/crm/clients/{client_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["idNumber"] == "987654321"
        assert data["firstName"] == "דוד"

    def test_list_clients(self, client):
        """Test listing all clients."""
        # Create two clients
        client.post(
            "/api/v1/crm/clients",
            json={"idNumber": "111111111", "fullName": "א"},
        )
        client.post(
            "/api/v1/crm/clients",
            json={"idNumber": "222222222", "fullName": "ב"},
        )

        response = client.get("/api/v1/crm/clients")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_update_client(self, client):
        """Test updating a client."""
        # Create a client
        create_response = client.post(
            "/api/v1/crm/clients",
            json={
                "idNumber": "333333333",
                "fullName": "שם ישן",
                "firstName": "שם",
                "lastName": "ישן",
            }
        )
        client_id = create_response.json()["id"]

        # Update it
        update_response = client.put(
            f"/api/v1/crm/clients/{client_id}",
            json={"lastName": "חדש", "phone": "0521111111"}
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["lastName"] == "חדש"
        assert data["phone"] == "0521111111"

    def test_get_nonexistent_client(self, client):
        """Test getting a client that doesn't exist."""
        response = client.get("/api/v1/crm/clients/99999")
        assert response.status_code == 404


class TestBeneficiaries:
    """Test client beneficiary operations."""

    def test_update_client_with_beneficiaries(self, client):
        """Test updating a client with beneficiaries."""
        # Create a client
        create_response = client.post(
            "/api/v1/crm/clients",
            json={
                "idNumber": "444444444",
                "fullName": "בעל מוטבים",
                "firstName": "בעל",
                "lastName": "מוטבים",
            }
        )
        client_id = create_response.json()["id"]

        # Update with beneficiaries
        update_response = client.put(
            f"/api/v1/crm/clients/{client_id}",
            json={
                "beneficiaries": [
                    {
                        "index": 1,
                        "firstName": "מוטב",
                        "lastName": "ראשון",
                        "idNumber": "555555555",
                        "birthDate": "2000-01-01",
                        "address": "תל אביב",
                        "relation": "בן/בת",
                        "percentage": 50.0,
                    },
                    {
                        "index": 2,
                        "firstName": "מוטב",
                        "lastName": "שני",
                        "idNumber": "666666666",
                        "birthDate": "2000-01-01",
                        "address": "תל אביב",
                        "relation": "בן/בת זוג",
                        "percentage": 50.0,
                    },
                ]
            }
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert len(data.get("beneficiaries", [])) == 2
