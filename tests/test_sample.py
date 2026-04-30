"""Tests for reqwatch.sample."""

from __future__ import annotations

import pytest

from reqwatch.core import RequestRecord
from reqwatch.sample import (
    sample_by_hash,
    sample_deterministic,
    sample_random,
    sample_rate,
    sample_summary,
)


def _make_record(request_id: str = "abc", method: str = "GET", url: str = "http://example.com") -> RequestRecord:
    return RequestRecord(
        request_id=request_id,
        timestamp="2024-01-01T00:00:00",
        method=method,
        url=url,
        request_headers={},
        request_body=None,
        response_status=200,
        response_headers={},
        response_body=None,
        duration_ms=10.0,
    )


RECORDS = [_make_record(request_id=str(i)) for i in range(20)]


class TestSampleRandom:
    def test_returns_correct_count(self):
        result = sample_random(RECORDS, 5, seed=42)
        assert len(result) == 5

    def test_returns_empty_for_zero(self):
        assert sample_random(RECORDS, 0) == []

    def test_returns_empty_for_negative(self):
        assert sample_random(RECORDS, -1) == []

    def test_caps_at_population_size(self):
        result = sample_random(RECORDS, 1000, seed=0)
        assert len(result) == len(RECORDS)

    def test_reproducible_with_seed(self):
        a = sample_random(RECORDS, 5, seed=7)
        b = sample_random(RECORDS, 5, seed=7)
        assert [r.request_id for r in a] == [r.request_id for r in b]


class TestSampleRate:
    def test_rate_zero_returns_empty(self):
        assert sample_rate(RECORDS, 0.0, seed=0) == []

    def test_rate_one_returns_all(self):
        assert len(sample_rate(RECORDS, 1.0, seed=0)) == len(RECORDS)

    def test_invalid_rate_raises(self):
        with pytest.raises(ValueError):
            sample_rate(RECORDS, 1.5)

    def test_roughly_half_at_point_five(self):
        result = sample_rate(RECORDS, 0.5, seed=99)
        assert 3 <= len(result) <= 17  # very loose bound for 20 items


class TestSampleDeterministic:
    def test_every_1_returns_all(self):
        assert sample_deterministic(RECORDS, 1) == RECORDS

    def test_every_2_returns_half(self):
        result = sample_deterministic(RECORDS, 2)
        assert len(result) == 10
        assert result[0].request_id == "0"
        assert result[1].request_id == "2"

    def test_every_n_less_than_1_raises(self):
        with pytest.raises(ValueError):
            sample_deterministic(RECORDS, 0)

    def test_empty_input(self):
        assert sample_deterministic([], 3) == []


class TestSampleByHash:
    def test_stable_across_calls(self):
        a = sample_by_hash(RECORDS, 0.5)
        b = sample_by_hash(RECORDS, 0.5)
        assert [r.request_id for r in a] == [r.request_id for r in b]

    def test_rate_zero_returns_empty(self):
        assert sample_by_hash(RECORDS, 0.0) == []

    def test_invalid_rate_raises(self):
        with pytest.raises(ValueError):
            sample_by_hash(RECORDS, -0.1)


class TestSampleSummary:
    def test_summary_format(self):
        sampled = RECORDS[:5]
        msg = sample_summary(RECORDS, sampled)
        assert "5/20" in msg
        assert "25.0%" in msg

    def test_empty_original(self):
        msg = sample_summary([], [])
        assert "0/0" in msg
        assert "0.0%" in msg
