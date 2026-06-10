import pytest
from datetime import datetime, timezone

from app.models import Client, ClientSignatureRequest
from app.services.justification_signing_complete_helpers import _create_signature_notification


pytestmark = pytest.mark.anyio


async def _create_crm_client(client) -> int:
    response = await client.post(
        "/api/v1/crm/clients",
        json={
            "idNumber": "888888888",
            "fullName": "לקוח בדיקות",
            "firstName": "לקוח",
            "lastName": "בדיקות",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


class TestJustificationSyncCrm:
    async def test_sync_crm_uses_latest_snapshot_and_creates_existing_product(self, client):
        client_id = await _create_crm_client(client)

        snapshot_payload_old = {
            "fundCode": "1111",
            "fundType": "גמל",
            "fundName": "קופה א",
            "fundNumber": "PN-100",
            "source": "AS",
            "amount": 100.0,
            "snapshotDate": "2024-01-01",
            "isActive": True,
        }
        snapshot_payload_new = {
            "fundCode": "1111",
            "fundType": "גמל",
            "fundName": "קופה א",
            "fundNumber": "PN-100",
            "source": "AS",
            "amount": 200.0,
            "snapshotDate": "2024-02-01",
            "isActive": True,
        }

        create_old = await client.post(
            f"/api/v1/crm/clients/{client_id}/snapshots",
            json=snapshot_payload_old,
        )
        assert create_old.status_code == 201

        create_new = await client.post(
            f"/api/v1/crm/clients/{client_id}/snapshots",
            json=snapshot_payload_new,
        )
        assert create_new.status_code == 201

        sync_response = await client.post(
            f"/api/v1/justification/clients/{client_id}/sync-crm",
        )
        assert sync_response.status_code == 200
        sync_data = sync_response.json()
        assert "detail" in sync_data
        assert "Synced" in sync_data["detail"]

        list_response = await client.get(
            f"/api/v1/justification/clients/{client_id}/existing-products"
        )
        assert list_response.status_code == 200
        items = list_response.json()
        assert len(items) == 1

        item = items[0]
        assert item["personalNumber"] == "PN-100"
        assert item["fundCode"] == "1111"
        assert item["fundName"] == "קופה א"
        assert item["fundType"] == "גמל"
        assert item["companyName"] == "אלטשולר-שחם"
        assert item["accumulatedAmount"] == 200.0

    async def test_sync_crm_with_no_snapshots_returns_zero(self, client):
        client_id = await _create_crm_client(client)

        sync_response = await client.post(
            f"/api/v1/justification/clients/{client_id}/sync-crm",
        )
        assert sync_response.status_code == 200
        assert sync_response.json().get("detail") == "Synced 0 products from CRM"

        list_response = await client.get(
            f"/api/v1/justification/clients/{client_id}/existing-products"
        )
        assert list_response.status_code == 200
        assert list_response.json() == []

    async def test_sync_crm_client_not_found(self, client):
        response = await client.post("/api/v1/justification/clients/9999/sync-crm")
        assert response.status_code == 404

    async def test_sync_all_crm_across_clients(self, client):
        client_id_1 = await _create_crm_client(client)
        create_second = await client.post(
            "/api/v1/crm/clients",
            json={
                "idNumber": "777777777",
                "fullName": "לקוח בדיקות 2",
                "firstName": "לקוח",
                "lastName": "בדיקות2",
            },
        )
        assert create_second.status_code == 201
        client_id_2 = create_second.json()["id"]

        snapshot_payload = {
            "fundCode": "3333",
            "fundType": "גמל",
            "fundName": "קופה ב",
            "fundNumber": "PN-200",
            "source": "AS",
            "amount": 123.0,
            "snapshotDate": "2024-03-01",
            "isActive": True,
        }
        create_snapshot = await client.post(
            f"/api/v1/crm/clients/{client_id_2}/snapshots",
            json=snapshot_payload,
        )
        assert create_snapshot.status_code == 201

        sync_response = await client.post("/api/v1/justification/sync-all-crm")
        assert sync_response.status_code == 200
        detail = sync_response.json().get("detail")
        assert isinstance(detail, str)
        assert "Synced" in detail
        assert "across" in detail

        list_1 = await client.get(f"/api/v1/justification/clients/{client_id_1}/existing-products")
        assert list_1.status_code == 200
        assert list_1.json() == []

        list_2 = await client.get(f"/api/v1/justification/clients/{client_id_2}/existing-products")
        assert list_2.status_code == 200
        items_2 = list_2.json()
        assert len(items_2) == 1
        assert items_2[0]["personalNumber"] == "PN-200"


class TestJustificationSigning:
    async def test_signature_status_tracks_latest_request(self, client, test_db):
        client_id = await _create_crm_client(client)

        empty_response = await client.get(
            f"/api/v1/justification/clients/{client_id}/packet-sign-status"
        )
        assert empty_response.status_code == 200
        assert empty_response.json() == {
            "status": "not_sent",
            "createdAt": None,
            "signedAt": None,
        }

        signed_at = datetime(2026, 6, 10, 9, 30, tzinfo=timezone.utc)
        request = ClientSignatureRequest(
            client_id=client_id,
            token="status-test-token",
            packet_filename="packet.pdf",
            signed_packet_filename="packet_signed.pdf",
            status="signed",
            signed_at=signed_at,
        )
        test_db.add(request)
        test_db.commit()

        status_response = await client.get(
            f"/api/v1/justification/clients/{client_id}/packet-sign-status"
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "signed"
        assert status_data["signedAt"].startswith("2026-06-10T09:30:00")

    async def test_signature_notification_appears_in_crm_reminders(self, client, test_db):
        client_id = await _create_crm_client(client)
        client_model = test_db.get(Client, client_id)
        request = ClientSignatureRequest(
            client_id=client_id,
            token="notification-test-token",
            packet_filename="packet.pdf",
            status="signed",
            signed_at=datetime.now(timezone.utc),
        )

        _create_signature_notification(test_db, client_model, request)

        reminders_response = await client.get("/api/v1/crm/reminders")
        assert reminders_response.status_code == 200
        reminders = reminders_response.json()
        assert len(reminders) == 1
        assert reminders[0]["clientId"] == client_id
        assert reminders[0]["note"] == "הלקוח חתם על חבילת המסמכים"

    async def test_create_sign_request_client_not_found(self, client):
        response = await client.post("/api/v1/justification/clients/9999/packet-sign-request")
        assert response.status_code == 404

    async def test_create_sign_request_missing_packet_returns_404(self, client):
        client_id = await _create_crm_client(client)
        response = await client.post(
            f"/api/v1/justification/clients/{client_id}/packet-sign-request"
        )
        assert response.status_code == 404
        assert response.json().get("detail") == "Client packet PDF not found"

    async def test_signing_link_and_submit_validation(self, client):
        response = await client.get("/api/v1/justification/client-sign/bad-token")
        assert response.status_code == 404

        pdf_response = await client.get("/api/v1/justification/client-sign/bad-token/packet.pdf")
        assert pdf_response.status_code == 404

        submit_response = await client.post(
            "/api/v1/justification/client-sign/bad-token/submit",
            json={"signatureDataUrl": ""},
        )
        assert submit_response.status_code in {400, 404}
