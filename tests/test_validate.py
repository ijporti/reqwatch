"""Tests for reqwatch.validate."""

import pytest
from reqwatch.core import RequestRecord
from reqwatch.validate import (
    ValidationResult,
    validate_record,
    validate_all,
    validation_summary,
)


def _make_record(
    method="GET",
    url="https://example.com/api",
    status_code=200,
    timestamp=1700000000.0,
):
    return RequestRecord(
        method=method,
        url=url,
        status_code=status_code,
        timestamp=timestamp,
        request_headers={},
        response_headers={},
        request_body=None,
        response_body=None,
        metadata={},
    )


class TestValidationResult:
    def test_is_valid_when_no_errors(self):
        r = _make_record()
        result = ValidationResult(record=r, errors=[])
        assert result.is_valid is True

    def test_not_valid_when_errors_present(self):
        r = _make_record()
        result = ValidationResult(record=r, errors=["bad method"])
        assert result.is_valid is False

    def test_summary_ok_format(self):
        r = _make_record()
        result = ValidationResult(record=r, errors=[])
        assert result.summary().startswith("[OK]")

    def test_summary_invalid_format(self):
        r = _make_record()
        result = ValidationResult(record=r, errors=["invalid URL: 'bad'"])
        assert "[INVALID]" in result.summary()
        assert "invalid URL" in result.summary()


class TestValidateRecord:
    def test_valid_record_passes(self):
        result = validate_record(_make_record())
        assert result.is_valid
        assert result.errors == []

    def test_invalid_method_reported(self):
        result = validate_record(_make_record(method="FETCH"))
        assert not result.is_valid
        assert any("method" in e for e in result.errors)

    def test_empty_method_reported(self):
        result = validate_record(_make_record(method=""))
        assert not result.is_valid

    def test_invalid_url_no_scheme(self):
        result = validate_record(_make_record(url="example.com/api"))
        assert not result.is_valid
        assert any("URL" in e for e in result.errors)

    def test_empty_url_reported(self):
        result = validate_record(_make_record(url=""))
        assert not result.is_valid

    def test_invalid_status_code_too_low(self):
        result = validate_record(_make_record(status_code=99))
        assert not result.is_valid
        assert any("status code" in e for e in result.errors)

    def test_invalid_status_code_too_high(self):
        result = validate_record(_make_record(status_code=600))
        assert not result.is_valid

    def test_none_status_code_allowed(self):
        result = validate_record(_make_record(status_code=None))
        assert result.is_valid

    def test_negative_timestamp_reported(self):
        result = validate_record(_make_record(timestamp=-1.0))
        assert not result.is_valid
        assert any("timestamp" in e for e in result.errors)

    def test_multiple_errors_collected(self):
        result = validate_record(_make_record(method="BAD", url="not-a-url"))
        assert len(result.errors) >= 2


class TestValidateAll:
    def test_empty_list_returns_empty(self):
        assert validate_all([]) == []

    def test_all_valid(self):
        records = [_make_record(), _make_record(method="POST")]
        results = validate_all(records)
        assert all(r.is_valid for r in results)

    def test_mixed_validity(self):
        records = [_make_record(), _make_record(url="bad")]
        results = validate_all(records)
        assert results[0].is_valid
        assert not results[1].is_valid


class TestValidationSummary:
    def test_empty_returns_no_records_message(self):
        msg = validation_summary([])
        assert "No records" in msg

    def test_all_valid_message(self):
        results = validate_all([_make_record(), _make_record()])
        msg = validation_summary(results)
        assert "valid" in msg
        assert "2" in msg

    def test_invalid_count_shown(self):
        records = [_make_record(), _make_record(url="oops")]
        results = validate_all(records)
        msg = validation_summary(results)
        assert "1 of 2" in msg
