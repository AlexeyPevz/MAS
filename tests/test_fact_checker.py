import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / 'root_mas' / 'root_mas'))

from tools.fact_checker import validate_sources


def test_validate_sources_ok():
    src = [{"url": "https://example.com", "title": "Example"}]
    assert validate_sources(src)


def test_validate_sources_bad():
    src = [{"url": "http://bad.com", "title": "Bad"}]
    assert not validate_sources(src)
