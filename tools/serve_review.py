#!/usr/bin/env python3
"""Serve local review media with single-range HTTP support."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
from typing import BinaryIO


class ReviewRequestHandler(SimpleHTTPRequestHandler):
    """Keep SimpleHTTPRequestHandler paths and directories, adding byte ranges."""

    _range_remaining: int | None = None
    _advertise_ranges = False

    def send_head(self) -> BinaryIO | None:
        path = self.translate_path(self.path)
        self._advertise_ranges = os.path.isfile(path)
        range_header = self.headers.get("Range")
        if range_header is None or not self._advertise_ranges:
            return super().send_head()

        try:
            source = open(path, "rb")
        except OSError:
            self.send_error(404, "File not found")
            return None
        try:
            size = os.fstat(source.fileno()).st_size
            selected = self._parse_range(range_header, size)
            if selected is None:
                source.close()
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return None
            start, end = selected
            source.seek(start)
            self._range_remaining = end - start + 1
            self.send_response(206)
            self.send_header("Content-type", self.guess_type(path))
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(self._range_remaining))
            self.send_header("Last-Modified", self.date_time_string(os.fstat(source.fileno()).st_mtime))
            self.end_headers()
            return source
        except Exception:
            source.close()
            raise

    def end_headers(self) -> None:
        if self._advertise_ranges:
            self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def copyfile(self, source: BinaryIO, outputfile: BinaryIO) -> None:
        remaining = self._range_remaining
        if remaining is None:
            shutil.copyfileobj(source, outputfile)
            return
        while remaining:
            chunk = source.read(min(64 * 1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)
        self._range_remaining = None

    @staticmethod
    def _parse_range(value: str, size: int) -> tuple[int, int] | None:
        if size <= 0 or not value.startswith("bytes="):
            return None
        specification = value[6:]
        if "," in specification or specification.count("-") != 1:
            return None
        first, last = specification.split("-", 1)
        try:
            if first:
                if not first.isdecimal() or (last and not last.isdecimal()):
                    return None
                start = int(first)
                end = size - 1 if not last else min(int(last), size - 1)
                if start >= size or end < start:
                    return None
                return start, end
            if not last.isdecimal():
                return None
            suffix = int(last)
            if suffix <= 0:
                return None
            return max(0, size - suffix), size - 1
        except (ValueError, OverflowError):
            return None


def _port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be in [1, 65535]")
    return port


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="document root to serve")
    parser.add_argument("--port", type=_port, required=True, help="TCP port")
    parser.add_argument("--bind", default="127.0.0.1", help="bind address (default: loopback)")
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"document root is not a directory: {root}")
    handler = partial(ReviewRequestHandler, directory=str(root))
    with ThreadingHTTPServer((args.bind, args.port), handler) as server:
        print(f"Serving {root} at http://{args.bind}:{args.port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
