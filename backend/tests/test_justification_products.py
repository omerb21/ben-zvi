"""Tests for justification products endpoints: saving, existing and new products.

These tests focus on basic happy-path flows without changing API behavior.
"""

import pytest


pytestmark = pytest.mark.anyio


async def _create_crm_client(client) -> int:
    response = await client.post(
        "/api/v1/crm/clients",
        json={
            "idNumber": "999999999",
            "fullName": "לקוח בדיקות",
            "firstName": "לקוח",
            "lastName": "בדיקות",
        },
    )
    assert response.status_code == 201
    data = response.json()
    return data["id"]


class TestSavingProducts:
    """Tests for saving products catalogue endpoints."""

    async def test_list_saving_products_initially_empty(self, client):
        response = await client.get("/api/v1/justification/saving-products")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_list_saving_products_after_sync_market(self, client):
        payload = [
            {
                "fundType": "גמל",
                "companyName": "חברה א",
                "fundName": "קופה א",
                "fundCode": "1111",
            },
            {
                "fundType": "גמל להשקעה",
                "companyName": "חברה ב",
                "fundName": "קופה ב",
                "fundCode": "2222",
            },
        ]

        sync_response = await client.post("/api/v1/admin/sync-market-products", json=payload)
        assert sync_response.status_code == 200

        list_response = await client.get("/api/v1/justification/saving-products")
        assert list_response.status_code == 200
        data = list_response.json()
        assert len(data) == 2
        codes = {item["fundCode"] for item in data}
        assert codes == {"1111", "2222"}


class TestExistingProducts:
    """Tests for existing products CRUD endpoints."""

    async def test_existing_product_crud_flow(self, client):
        client_id = await _create_crm_client(client)

        create_response = await client.post(
            f"/api/v1/justification/clients/{client_id}/existing-products",
            json={
                "fundType": "גמל",
                "companyName": "חברה קיימת",
                "fundName": "קופה קיימת",
                "fundCode": "EX123",
                "personalNumber": "PN-1",
            },
        )
        assert create_response.status_code == 201
        created = create_response.json()
        existing_id = created["id"]

        list_response = await client.get(
            f"/api/v1/justification/clients/{client_id}/existing-products"
        )
        assert list_response.status_code == 200
        items = list_response.json()
        assert len(items) == 1
        assert items[0]["fundCode"] == "EX123"

        update_response = await client.patch(
            f"/api/v1/justification/existing-products/{existing_id}",
            json={"employmentStatus": "עובד"},
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["employmentStatus"] == "עובד"

        delete_response = await client.delete(
            f"/api/v1/justification/existing-products/{existing_id}"
        )
        assert delete_response.status_code == 204

        list_after_delete = await client.get(
            f"/api/v1/justification/clients/{client_id}/existing-products"
        )
        assert list_after_delete.status_code == 200
        assert list_after_delete.json() == []


class TestNewProductsAndForms:
    """Tests for new products and their form instances endpoints."""

    async def test_new_product_and_form_instance_flow(self, client):
        client_id = await _create_crm_client(client)

        new_product_response = await client.post(
            f"/api/v1/justification/clients/{client_id}/new-products",
            json={
                "fundType": "גמל",
                "companyName": "חברה חדשה",
                "fundName": "קופה חדשה",
                "fundCode": "NP123",
            },
        )
        assert new_product_response.status_code == 201
        new_product = new_product_response.json()
        new_product_id = new_product["id"]

        list_new_response = await client.get(
            f"/api/v1/justification/clients/{client_id}/new-products"
        )
        assert list_new_response.status_code == 200
        new_items = list_new_response.json()
        assert any(item["id"] == new_product_id for item in new_items)

        form_create_response = await client.post(
            f"/api/v1/justification/new-products/{new_product_id}/form-instances",
            json={"templateFilename": "dummy.pdf"},
        )
        assert form_create_response.status_code == 201
        form_instance = form_create_response.json()
        form_id = form_instance["id"]

        list_forms_response = await client.get(
            f"/api/v1/justification/new-products/{new_product_id}/form-instances"
        )
        assert list_forms_response.status_code == 200
        form_items = list_forms_response.json()
        assert len(form_items) == 1
        assert form_items[0]["id"] == form_id

        delete_form_response = await client.delete(
            f"/api/v1/justification/form-instances/{form_id}"
        )
        assert delete_form_response.status_code == 204

        list_forms_after_delete = await client.get(
            f"/api/v1/justification/new-products/{new_product_id}/form-instances"
        )
        assert list_forms_after_delete.status_code == 200
        assert list_forms_after_delete.json() == []

        delete_new_response = await client.delete(
            f"/api/v1/justification/new-products/{new_product_id}"
        )
        assert delete_new_response.status_code == 204
