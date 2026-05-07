"""Tests for reqwatch.chain."""

from __future__ import annotations

import pytest

from reqwatch.core import RequestRecord
from reqwatch.chain import (
    ChainStep,
    ChainResult,
    build_chain,
    run_chain,
    chain_summary,
)


def _make_record(method: str = "GET", url: str = "http://example.com", status: int = 200) -> RequestRecord:
    return RequestRecord(
        method=method,
        url=url,
        request_headers={},
        request_body="",
        response_headers={},
        response_body="",
        status_code=status,
        timestamp="2024-01-01T00:00:00",
        duration_ms=10.0,
    )


class TestChainResult:
    def test_succeeded_when_no_error(self):
        r = ChainResult(steps=[], outputs=[], error=None)
        assert r.succeeded is True

    def test_not_succeeded_when_error(self):
        r = ChainResult(steps=[], outputs=[], error="boom")
        assert r.succeeded is False

    def test_length_matches_steps(self):
        steps = [ChainStep(record=_make_record()) for _ in range(3)]
        r = ChainResult(steps=steps)
        assert r.length == 3

    def test_summary_success(self):
        steps = [ChainStep(record=_make_record())]
        r = ChainResult(steps=steps, outputs=[_make_record()])
        assert "1/1" in r.summary()

    def test_summary_failure(self):
        r = ChainResult(steps=[], outputs=[], error="timeout")
        assert "timeout" in r.summary()


class TestBuildChain:
    def test_creates_steps_for_each_record(self):
        records = [_make_record() for _ in range(4)]
        steps = build_chain(records)
        assert len(steps) == 4

    def test_no_transforms_by_default(self):
        records = [_make_record()]
        steps = build_chain(records)
        assert steps[0].transform is None

    def test_assigns_transforms(self):
        records = [_make_record(), _make_record()]
        transforms = [lambda r: r, None]
        steps = build_chain(records, transforms=transforms)
        assert steps[0].transform is not None
        assert steps[1].transform is None

    def test_pads_missing_transforms(self):
        records = [_make_record(), _make_record(), _make_record()]
        steps = build_chain(records, transforms=[lambda r: r])
        assert steps[1].transform is None
        assert steps[2].transform is None


class TestRunChain:
    def test_outputs_equal_steps_on_success(self):
        records = [_make_record() for _ in range(3)]
        steps = build_chain(records)
        result = run_chain(steps)
        assert result.succeeded
        assert len(result.outputs) == 3

    def test_transform_is_applied(self):
        record = _make_record(method="get")

        def upper_method(r: RequestRecord) -> RequestRecord:
            from dataclasses import replace
            return replace(r, method="GET_MODIFIED")

        steps = build_chain([record], transforms=[upper_method])
        result = run_chain(steps)
        assert result.outputs[0].method == "GET_MODIFIED"

    def test_error_captured_on_exception(self):
        def bad_transform(r):
            raise ValueError("intentional error")

        steps = build_chain([_make_record()], transforms=[bad_transform])
        result = run_chain(steps)
        assert not result.succeeded
        assert "intentional error" in result.error

    def test_empty_chain_succeeds(self):
        result = run_chain([])
        assert result.succeeded
        assert result.outputs == []


def test_chain_summary_delegates_to_result():
    steps = [ChainStep(record=_make_record())]
    r = ChainResult(steps=steps, outputs=[_make_record()])
    assert chain_summary(r) == r.summary()
