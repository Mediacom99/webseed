"""Layer 1: Database Store tests — direct PostgresStore operations."""

from __future__ import annotations

from webseed.db.store import PostgresStore
from webseed.models import PipelineStatus

from tests.conftest import make_biz


class TestUpsertBusiness:
    def test_insert_returns_inserted(self, store: PostgresStore) -> None:
        biz = make_biz()
        result = store.upsert_business(biz, "test_run")
        assert result == "inserted"

    def test_update_returns_updated(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "test_run")
        biz.rating = 3.0
        result = store.upsert_business(biz, "test_run_2")
        assert result == "updated"

    def test_update_changes_mutable_fields(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run1")
        biz.rating = 1.5
        biz.reviews = 99
        store.upsert_business(biz, "run2")
        rec = store.find_by_place_id(biz.place_id)
        assert rec is not None
        assert rec.rating == 1.5
        assert rec.reviews == 99


class TestFindByPlaceId:
    def test_returns_correct_record(self, store: PostgresStore) -> None:
        biz = make_biz(name="Ristorante Bella", rating=4.8, reviews=100)
        store.upsert_business(biz, "run")
        rec = store.find_by_place_id(biz.place_id)
        assert rec is not None
        assert rec.name == "Ristorante Bella"
        assert rec.rating == 4.8
        assert rec.reviews == 100
        assert rec.place_id == biz.place_id
        assert rec.status == "searched"
        assert rec.id  # UUID should be set

    def test_returns_none_for_missing(self, store: PostgresStore) -> None:
        assert store.find_by_place_id("NONEXISTENT_PLACE") is None


class TestFindByName:
    def test_ilike_partial_match(self, store: PostgresStore) -> None:
        biz = make_biz(name="Pizzeria Napoletana Test")
        store.upsert_business(biz, "run")
        results = store.find_by_name("napoletana")
        assert any(r.place_id == biz.place_id for r in results)

    def test_returns_empty_for_no_match(self, store: PostgresStore) -> None:
        results = store.find_by_name("ZZZNONEXISTENT999")
        assert results == []


class TestResolveIdentifier:
    def test_by_place_id(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run")
        results = store.resolve_identifier(biz.place_id)
        assert len(results) == 1
        assert results[0].place_id == biz.place_id

    def test_falls_back_to_name(self, store: PostgresStore) -> None:
        biz = make_biz(name="UniqueResolveTest123")
        store.upsert_business(biz, "run")
        results = store.resolve_identifier("UniqueResolveTest123")
        assert len(results) >= 1
        assert any(r.place_id == biz.place_id for r in results)


class TestUpdateStatus:
    def test_changes_status(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run")
        ok = store.update_status(biz.place_id, PipelineStatus.ENRICHED)
        assert ok is True
        rec = store.find_by_place_id(biz.place_id)
        assert rec is not None
        assert rec.status == "enriched"

    def test_with_extra_fields(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run")
        store.update_status(biz.place_id, PipelineStatus.DEPLOYED, {"vercel_url": "https://test.vercel.app"})
        rec = store.find_by_place_id(biz.place_id)
        assert rec is not None
        assert rec.vercel_url == "https://test.vercel.app"

    def test_updated_at_changes(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run")
        rec1 = store.find_by_place_id(biz.place_id)
        assert rec1 is not None
        store.update_status(biz.place_id, PipelineStatus.ENRICHED)
        rec2 = store.find_by_place_id(biz.place_id)
        assert rec2 is not None
        assert rec2.updated_at >= rec1.updated_at

    def test_returns_false_for_missing(self, store: PostgresStore) -> None:
        ok = store.update_status("NONEXISTENT", PipelineStatus.ENRICHED)
        assert ok is False


class TestAllPlaceIds:
    def test_contains_test_place_id(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run")
        ids = store.all_place_ids()
        assert biz.place_id in ids


class TestGetAllBusinesses:
    def test_unfiltered(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run")
        all_biz = store.get_all_businesses()
        assert any(r.place_id == biz.place_id for r in all_biz)

    def test_with_status_filter(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run")
        store.update_status(biz.place_id, PipelineStatus.ENRICHED)
        enriched = store.get_all_businesses(status="enriched")
        assert any(r.place_id == biz.place_id for r in enriched)
        searched = store.get_all_businesses(status="searched")
        assert not any(r.place_id == biz.place_id for r in searched)


class TestDeleteBusiness:
    def test_returns_true_and_removes(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run")
        assert store.delete_business(biz.place_id) is True
        assert store.find_by_place_id(biz.place_id) is None

    def test_returns_false_for_missing(self, store: PostgresStore) -> None:
        assert store.delete_business("NONEXISTENT") is False


class TestBlacklist:
    def test_opted_out_in_blacklist(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run")
        store.update_status(biz.place_id, PipelineStatus.OPTED_OUT)
        blacklist = store.get_blacklisted_place_ids()
        assert biz.place_id in blacklist


class TestSettings:
    def test_get_seeded_prompt(self, store: PostgresStore) -> None:
        val = store.get_setting("prompt.site_gen")
        assert val is not None
        assert len(val) > 0

    def test_upsert_create_and_update(self, store: PostgresStore) -> None:
        test_key = "test.temp_setting_123"
        try:
            store.upsert_setting(test_key, "v1", "test setting")
            assert store.get_setting(test_key) == "v1"
            store.upsert_setting(test_key, "v2")
            assert store.get_setting(test_key) == "v2"
        finally:
            store.delete_setting(test_key)

    def test_list_prompt_prefix(self, store: PostgresStore) -> None:
        settings = store.list_settings(prefix="prompt")
        assert len(settings) > 0
        assert all(s["key"].startswith("prompt.") for s in settings)

    def test_list_config_prefix(self, store: PostgresStore) -> None:
        settings = store.list_settings(prefix="config")
        assert len(settings) > 0
        assert all(s["key"].startswith("config.") for s in settings)

    def test_delete_setting(self, store: PostgresStore) -> None:
        test_key = "test.delete_me_123"
        store.upsert_setting(test_key, "temp")
        assert store.delete_setting(test_key) is True
        assert store.get_setting(test_key) is None

    def test_delete_nonexistent(self, store: PostgresStore) -> None:
        assert store.delete_setting("test.nonexistent_xyz") is False


class TestResetStaleRunning:
    def test_resets_running_to_error(self, store: PostgresStore) -> None:
        biz = make_biz()
        store.upsert_business(biz, "run")
        store.update_status(biz.place_id, PipelineStatus.RUNNING_ENRICH)
        count = store.reset_stale_running()
        assert count >= 1
        rec = store.find_by_place_id(biz.place_id)
        assert rec is not None
        assert rec.status == "error_enrich"


class TestLogEvent:
    def test_insert_no_exception(self, store: PostgresStore) -> None:
        store.log_event(
            job_id="test-job-123",
            place_id="TEST_PLACE_log",
            event_type="step_start",
            step="search",
            message="Test event",
            data={"key": "value"},
        )
