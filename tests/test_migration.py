"""Layer 5: Migration verification — check tables, seeds, and prompt integrity."""

from __future__ import annotations

from sqlalchemy import inspect, text

from webseed.db.store import PostgresStore

from tests.conftest import DATABASE_URL


EXPECTED_PROMPT_KEYS = [
    "prompt.site_gen",
    "prompt.site_gen_system",
    "prompt.site_gen_photos",
    "prompt.site_gen_no_photos",
    "prompt.code_review",
    "prompt.code_review_system",
    "prompt.visual_test",
    "prompt.visual_test_system",
    "prompt.fix_html",
    "prompt.fix_html_system",
    "prompt.email_gen",
    "prompt.email_gen_system",
]

EXPECTED_CONFIG_KEYS = {
    "config.contact_email": "",
    "config.sender_name": "Edoardo di WebSeed",
    "config.default_model": "sonnet",
    "config.test_model": "sonnet",
    "config.max_fix_iterations": "3",
    "config.gmail_label_name": "webseed-queue",
    "config.max_photos": "3",
    "config.timeout_generate": "120",
    "config.timeout_test": "120",
    "config.timeout_email": "180",
}


class TestTablesExist:
    def test_all_three_tables(self, store: PostgresStore) -> None:
        inspector = inspect(store._engine)
        tables = inspector.get_table_names()
        assert "businesses" in tables
        assert "settings" in tables
        assert "event_log" in tables


class TestSettingsCount:
    def test_total_seed_count(self, store: PostgresStore) -> None:
        all_settings = store.list_settings()
        # 12 prompts + 10 configs = 22
        # But there may be test-created settings, so check >= 22
        prompt_count = sum(1 for s in all_settings if s["key"].startswith("prompt."))
        config_count = sum(1 for s in all_settings if s["key"].startswith("config."))
        assert prompt_count == 12, f"Expected 12 prompts, got {prompt_count}"
        assert config_count >= 10, f"Expected >=10 configs, got {config_count}"


class TestPromptKeys:
    def test_each_prompt_exists_nonempty(self, store: PostgresStore) -> None:
        for key in EXPECTED_PROMPT_KEYS:
            val = store.get_setting(key)
            assert val is not None, f"Missing prompt: {key}"
            assert len(val) > 0, f"Empty prompt: {key}"


class TestConfigDefaults:
    def test_each_config_has_correct_default(self, store: PostgresStore) -> None:
        for key, expected in EXPECTED_CONFIG_KEYS.items():
            val = store.get_setting(key)
            assert val is not None, f"Missing config: {key}"
            # contact_email may have been modified by tests, skip value check
            if key != "config.contact_email":
                assert val == expected, f"Config {key}: expected '{expected}', got '{val}'"


class TestPromptFormatSafety:
    def test_site_gen_has_name_placeholder(self, store: PostgresStore) -> None:
        val = store.get_setting("prompt.site_gen")
        assert val is not None
        assert "{name}" in val

    def test_prompts_use_double_braces_for_literals(self, store: PostgresStore) -> None:
        """Prompts that use .format() must use {{ }} for literal braces."""
        # code_review and visual_test prompts have JSON examples with literal braces
        for key in ["prompt.code_review", "prompt.visual_test"]:
            val = store.get_setting(key)
            assert val is not None
            # These prompts contain JSON result templates with {{pass}} etc.
            # Verify they use {{ not just {
            if '"pass"' in val:
                assert '{{' in val, f"{key} uses single braces in JSON template — will break .format()"
