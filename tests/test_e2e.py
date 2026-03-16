"""Layer 6: E2E smoke test — partial pipeline flow through the API."""

from __future__ import annotations

from starlette.testclient import TestClient

from webseed.db.store import PostgresStore

from tests.conftest import make_biz


class TestE2EFlow:
    def test_partial_pipeline_via_api(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """Simulate pipeline flow: insert → list → status update → blacklist → hard-delete."""
        store: PostgresStore = client.app.state.store  # type: ignore[union-attr]

        # 1. Insert fake business via store (status=searched)
        biz = make_biz()
        store.upsert_business(biz, "e2e_run")

        # 2. GET /businesses → verify it appears
        resp = client.get("/businesses", headers=auth_headers)
        assert resp.status_code == 200
        place_ids = [b["place_id"] for b in resp.json()]
        assert biz.place_id in place_ids

        # 3. PATCH status → enriched
        resp = client.patch(
            f"/businesses/{biz.place_id}/status",
            json={"to": "enriched"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # 4. GET → verify status=enriched
        resp = client.get(f"/businesses/{biz.place_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "enriched"

        # 5. POST blacklist → opted_out
        resp = client.post(f"/businesses/{biz.place_id}/blacklist", headers=auth_headers)
        assert resp.status_code == 200
        resp = client.get(f"/businesses/{biz.place_id}", headers=auth_headers)
        assert resp.json()["status"] == "opted_out"

        # 6. DELETE blacklist → back to searched
        resp = client.delete(f"/businesses/{biz.place_id}/blacklist", headers=auth_headers)
        assert resp.status_code == 200
        resp = client.get(f"/businesses/{biz.place_id}", headers=auth_headers)
        assert resp.json()["status"] == "searched"

        # 7. POST hard-delete → verify gone
        resp = client.post(
            "/businesses/hard-delete",
            json={"place_ids": [biz.place_id]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        resp = client.get(f"/businesses/{biz.place_id}", headers=auth_headers)
        assert resp.status_code == 404
