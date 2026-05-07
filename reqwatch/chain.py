"""Chain multiple request records into a sequential replay pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from reqwatch.core import RequestRecord


@dataclass
class ChainStep:
    record: RequestRecord
    transform: Optional[Callable[[RequestRecord], RequestRecord]] = None

    def apply(self) -> RequestRecord:
        if self.transform is not None:
            return self.transform(self.record)
        return self.record


@dataclass
class ChainResult:
    steps: List[ChainStep]
    outputs: List[RequestRecord] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.error is None

    @property
    def length(self) -> int:
        return len(self.steps)

    def summary(self) -> str:
        if not self.succeeded:
            return f"Chain failed: {self.error}"
        return f"Chain executed {len(self.outputs)}/{self.length} steps successfully"


def build_chain(records: List[RequestRecord],
                transforms: Optional[List[Optional[Callable[[RequestRecord], RequestRecord]]]] = None
                ) -> List[ChainStep]:
    """Pair each record with an optional transform to create a chain of steps."""
    if transforms is None:
        transforms = [None] * len(records)
    if len(transforms) < len(records):
        transforms = list(transforms) + [None] * (len(records) - len(transforms))
    return [ChainStep(record=r, transform=t) for r, t in zip(records, transforms)]


def run_chain(steps: List[ChainStep]) -> ChainResult:
    """Execute each step in order, collecting outputs."""
    result = ChainResult(steps=steps)
    try:
        for step in steps:
            output = step.apply()
            result.outputs.append(output)
    except Exception as exc:  # noqa: BLE001
        result.error = str(exc)
    return result


def chain_summary(result: ChainResult) -> str:
    """Return a human-readable summary of the chain execution."""
    return result.summary()
