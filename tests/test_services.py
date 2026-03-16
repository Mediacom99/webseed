"""Layer 4: Services tests — management service functions with real DB."""

from __future__ import annotations

from webseed import services
from webseed.db.store import PostgresStore
from webseed.models import PipelineStatus
from webseed.storage import LocalFileStorage

from tests.conftest import make_biz


class TestGetBusiness:
    def test_returns_record(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run")
        rec = services.get_business(store, biz.place_id)
        assert rec is not None
        assert rec.name == biz.name

    def test_returns_none_for_missing(self, store: PostgresStore) -> None:
        assert services.get_business(store, "NONEXISTENT") is None


class TestListBusinesses:
    def test_with_status_filter(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run")
        store.update_status(biz.place_id, PipelineStatus.ENRICHED)
        results = services.list_businesses(store, status="enriched")
        assert any(r.place_id == biz.place_id for r in results)


class TestGetStats:
    def test_has_total(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run")
        stats = services.get_stats(store)
        assert "total" in stats
        assert stats["total"] >= 1


class TestResetStatus:
    def test_changes_status(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run")
        ok = services.reset_status(store, biz.place_id, PipelineStatus.ENRICHED)
        assert ok is True
        rec = store.find_by_place_id(biz.place_id)
        assert rec is not None
        assert rec.status == "enriched"


class TestBlacklist:
    def test_add_and_remove(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run")
        count = services.blacklist_add(store, [biz.place_id])
        assert count == 1
        rec = store.find_by_place_id(biz.place_id)
        assert rec is not None
        assert rec.status == "opted_out"

        ok = services.blacklist_remove(store, biz.place_id)
        assert ok is True
        rec2 = store.find_by_place_id(biz.place_id)
        assert rec2 is not None
        assert rec2.status == "searched"


class TestExportCsv:
    def test_csv_has_headers(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run")
        csv_str = services.export_csv(store)
        assert "place_id" in csv_str
        assert "name" in csv_str
        assert "status" in csv_str
        assert biz.place_id in csv_str
