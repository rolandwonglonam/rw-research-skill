"""Expose the packaged search-strategy tests to repository CI."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_FILE = ROOT / "skills" / "rw-search-strategy" / "tests" / "test_search_strategy.py"


def load_tests(loader, tests, pattern):
    spec = importlib.util.spec_from_file_location("packaged_search_strategy_tests", TEST_FILE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return loader.loadTestsFromModule(module)
