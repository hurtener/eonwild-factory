"""Fast default test run: tests listed in slow_tests.txt (>= 1 s each) are marked `slow` and
deselected by pyproject's addopts. Full suite: pytest -m "" ."""
from pathlib import Path

import pytest

_SLOW = {line.strip() for line in (Path(__file__).parent / "slow_tests.txt").read_text().splitlines()
         if line.strip() and not line.startswith("#")}


def pytest_collection_modifyitems(items):
    for item in items:
        if item.nodeid in _SLOW:
            item.add_marker(pytest.mark.slow)
