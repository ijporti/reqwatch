"""Integration tests for route grouping with real-world URL patterns."""

from reqwatch.core import RequestRecord
from reqwatch.route import route_records


def _make_record(method: str = "GET", url: str = "http://api.local/", status: int = 200) -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=status,
        response_headers={},
        response_body=None,
        timestamp="2024-06-01T12:00:00",
    )


class TestRouteIntegration:
    def test_mixed_routes_grouped_correctly(self):
        records = [
            _make_record(url="http://api.local/users/1"),
            _make_record(url="http://api.local/users/2"),
            _make_record(url="http://api.local/orders/99"),
            _make_record(url="http://api.local/health"),
        ]
        result = route_records(records, ["/users/{id}", "/orders/{id}", "/health"])
        assert len(result.groups["/users/{id}"]) == 2
        assert len(result.groups["/orders/{id}"]) == 1
        assert len(result.groups["/health"]) == 1
        assert len(result.groups["<unmatched>"]) == 0

    def test_all_unmatched_when_no_templates_match(self):
        records = [
            _make_record(url="http://api.local/foo"),
            _make_record(url="http://api.local/bar"),
        ]
        result = route_records(records, ["/users/{id}"])
        assert len(result.groups["<unmatched>"]) == 2

    def test_empty_records_no_error(self):
        result = route_records([], ["/users/{id}"])
        assert not result.has_error
        assert result.groups["/users/{id}"] == []

    def test_summary_contains_all_templates(self):
        r = _make_record(url="http://api.local/items/5")
        result = route_records([r], ["/items/{id}", "/other"])
        s = result.summary()
        assert "/items/{id}" in s
        assert "/other" in s
