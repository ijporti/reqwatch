"""Tests for reqwatch.normalize."""

import pytest
from reqwatch.core import RequestRecord
from reqwatch.normalize import (
    normalize_method,
    normalize_url,
    normalize_headers,
    apply_normalizations,
    normalization_summary,
)


def _make_record(
    method="get",
    url="HTTP://Example.COM/api/v1/",
    status=200,
    request_headers=None,
    response_headers=None,
):
    return RequestRecord(
        method=method,
        url=url,
        status_code=status,
        request_headers=request_headers or {"Content-Type": "application/json"},
        response_headers=response_headers or {"X-Request-Id": "abc"},
        request_body=None,
        response_body=None,
        timestamp="2024-01-01T00:00:00",
        duration_ms=10.0,
        metadata={},
    )


class TestNormalizeMethod:
    def test_lowercased_method_is_uppercased(self):
        r = normalize_method(_make_record(method="get"))
        assert r.method == "GET"

    def test_already_uppercase_unchanged(self):
        r = normalize_method(_make_record(method="POST"))
        assert r.method == "POST"

    def test_mixed_case_uppercased(self):
        r = normalize_method(_make_record(method="pAtCh"))
        assert r.method == "PATCH"

    def test_original_not_mutated(self):
        original = _make_record(method="delete")
        normalize_method(original)
        assert original.method == "delete"


class TestNormalizeUrl:
    def test_scheme_lowercased(self):
        r = normalize_url(_make_record(url="HTTP://example.com/path"))
        assert r.url.startswith("http://")

    def test_host_lowercased(self):
        r = normalize_url(_make_record(url="https://EXAMPLE.COM/path"))
        assert "example.com" in r.url

    def test_trailing_slash_stripped(self):
        r = normalize_url(_make_record(url="https://example.com/api/v1/"))
        assert not r.url.endswith("/")

    def test_trailing_slash_kept_when_disabled(self):
        r = normalize_url(
            _make_record(url="https://example.com/api/v1/"),
            strip_trailing_slash=False,
        )
        assert r.url.endswith("/")

    def test_original_not_mutated(self):
        original = _make_record(url="HTTP://EXAMPLE.COM/api/")
        normalize_url(original)
        assert original.url == "HTTP://EXAMPLE.COM/api/"


class TestNormalizeHeaders:
    def test_header_names_lowercased(self):
        r = normalize_headers(
            _make_record(request_headers={"Content-Type": "application/json"})
        )
        assert "content-type" in r.request_headers

    def test_remove_keys_excluded(self):
        r = normalize_headers(
            _make_record(request_headers={"Authorization": "Bearer x", "Accept": "*/*"}),
            remove_keys=["authorization"],
        )
        assert "authorization" not in r.request_headers
        assert "accept" in r.request_headers

    def test_response_headers_also_normalized(self):
        r = normalize_headers(
            _make_record(response_headers={"X-Request-Id": "abc"})
        )
        assert "x-request-id" in r.response_headers


class TestApplyNormalizations:
    def test_all_normalizations_applied(self):
        record = _make_record(
            method="post",
            url="HTTPS://API.EXAMPLE.COM/v2/items/",
            request_headers={"Authorization": "Bearer tok", "Content-Type": "application/json"},
        )
        result = apply_normalizations(record, remove_header_keys=["authorization"])
        assert result.method == "POST"
        assert result.url.startswith("https://")
        assert not result.url.endswith("/")
        assert "authorization" not in result.request_headers


class TestNormalizationSummary:
    def test_no_changes_message(self):
        r = _make_record(method="GET", url="https://example.com/path")
        msg = normalization_summary(r, r)
        assert "No changes" in msg

    def test_method_change_shown(self):
        original = _make_record(method="get")
        normalized = normalize_method(original)
        msg = normalization_summary(original, normalized)
        assert "method" in msg

    def test_url_change_shown(self):
        original = _make_record(url="HTTP://EXAMPLE.COM/api/")
        normalized = normalize_url(original)
        msg = normalization_summary(original, normalized)
        assert "url" in msg
