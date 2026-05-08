"""Tests for reqwatch.audit."""
import json
import os
import pytest

from reqwatch.audit import (
    AuditEntry,
    AuditLog,
    add_entry,
    audit_summary,
    load_audit_log,
    save_audit_log,
)


# ---------------------------------------------------------------------------
# add_entry
# ---------------------------------------------------------------------------

class TestAddEntry:
    def test_returns_new_log_with_entry(self):
        log = AuditLog()
        result = add_entry(log, "mask")
        assert len(result.entries) == 1
        assert result.entries[0].operation == "mask"

    def test_does_not_mutate_original(self):
        log = AuditLog()
        add_entry(log, "mask")
        assert len(log.entries) == 0

    def test_details_stored(self):
        log = AuditLog()
        result = add_entry(log, "filter", {"method": "GET"})
        assert result.entries[0].details == {"method": "GET"}

    def test_empty_details_when_none(self):
        log = AuditLog()
        result = add_entry(log, "replay")
        assert result.entries[0].details == {}

    def test_timestamp_is_set(self):
        log = AuditLog()
        result = add_entry(log, "trim")
        assert result.entries[0].timestamp != ""

    def test_multiple_entries_accumulate(self):
        log = AuditLog()
        log = add_entry(log, "op1")
        log = add_entry(log, "op2")
        assert len(log.entries) == 2
        assert log.entries[1].operation == "op2"


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------

class TestSaveLoad:
    def test_roundtrip_preserves_operation(self, tmp_path):
        path = str(tmp_path / "audit.json")
        log = add_entry(AuditLog(), "merge", {"count": 5})
        save_audit_log(log, path)
        loaded = load_audit_log(path)
        assert loaded.entries[0].operation == "merge"

    def test_roundtrip_preserves_details(self, tmp_path):
        path = str(tmp_path / "audit.json")
        log = add_entry(AuditLog(), "patch", {"field": "url"})
        save_audit_log(log, path)
        loaded = load_audit_log(path)
        assert loaded.entries[0].details == {"field": "url"}

    def test_missing_file_returns_empty_log(self, tmp_path):
        path = str(tmp_path / "nonexistent.json")
        log = load_audit_log(path)
        assert log.entries == []

    def test_saved_file_is_valid_json(self, tmp_path):
        path = str(tmp_path / "audit.json")
        log = add_entry(AuditLog(), "snapshot")
        save_audit_log(log, path)
        with open(path) as fh:
            data = json.load(fh)
        assert isinstance(data, list)
        assert data[0]["operation"] == "snapshot"


# ---------------------------------------------------------------------------
# audit_summary
# ---------------------------------------------------------------------------

class TestAuditSummary:
    def test_empty_log_message(self):
        assert audit_summary(AuditLog()) == "audit log: no entries"

    def test_single_entry_singular_word(self):
        log = add_entry(AuditLog(), "replay")
        assert "1 entry" in audit_summary(log)

    def test_multiple_entries_plural_word(self):
        log = add_entry(AuditLog(), "replay")
        log = add_entry(log, "mask")
        assert "2 entries" in audit_summary(log)

    def test_operations_appear_in_summary(self):
        log = add_entry(AuditLog(), "trim", {"n": 10})
        s = audit_summary(log)
        assert "trim" in s
