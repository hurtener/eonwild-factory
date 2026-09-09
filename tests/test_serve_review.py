from __future__ import annotations

from contextlib import contextmanager
from functools import partial
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import importlib.util
from pathlib import Path
import threading

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("serve_review", ROOT / "tools/serve_review.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@contextmanager
def review_server(root: Path):
    handler = partial(MODULE.ReviewRequestHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request(port: int, method: str, path: str, *, range_value: str | None = None):
    headers = {} if range_value is None else {"Range": range_value}
    connection = HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        connection.request(method, path, headers=headers)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


@pytest.fixture
def media_root(tmp_path: Path) -> Path:
    (tmp_path / "clip.bin").write_bytes(b"0123456789")
    return tmp_path


def test_normal_get_and_directory_behavior_use_explicit_root(media_root: Path):
    with review_server(media_root) as port:
        status, headers, body = request(port, "GET", "/clip.bin")
        listing_status, _, listing = request(port, "GET", "/")
    assert status == 200
    assert headers["Accept-Ranges"] == "bytes"
    assert body == b"0123456789"
    assert listing_status == 200
    assert b"clip.bin" in listing


@pytest.mark.parametrize(
    ("range_value", "expected_range", "expected_body"),
    [
        ("bytes=2-5", "bytes 2-5/10", b"2345"),
        ("bytes=7-", "bytes 7-9/10", b"789"),
        ("bytes=-3", "bytes 7-9/10", b"789"),
        ("bytes=-30", "bytes 0-9/10", b"0123456789"),
    ],
)
def test_single_byte_range_get(media_root, range_value, expected_range, expected_body):
    with review_server(media_root) as port:
        status, headers, body = request(port, "GET", "/clip.bin", range_value=range_value)
    assert status == 206
    assert headers["Content-Range"] == expected_range
    assert headers["Content-Length"] == str(len(expected_body))
    assert headers["Accept-Ranges"] == "bytes"
    assert body == expected_body


def test_range_head_returns_headers_without_body(media_root: Path):
    with review_server(media_root) as port:
        status, headers, body = request(port, "HEAD", "/clip.bin", range_value="bytes=1-3")
    assert status == 206
    assert headers["Content-Range"] == "bytes 1-3/10"
    assert headers["Content-Length"] == "3"
    assert headers["Accept-Ranges"] == "bytes"
    assert body == b""


@pytest.mark.parametrize(
    "range_value",
    ["items=0-1", "bytes=", "bytes=5-2", "bytes=10-", "bytes=-0", "bytes=0-1,4-5"],
)
def test_invalid_or_unsatisfiable_range_is_416(media_root: Path, range_value: str):
    with review_server(media_root) as port:
        status, headers, body = request(port, "GET", "/clip.bin", range_value=range_value)
    assert status == 416
    assert headers["Content-Range"] == "bytes */10"
    assert headers["Content-Length"] == "0"
    assert headers["Accept-Ranges"] == "bytes"
    assert body == b""
