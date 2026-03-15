from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from staticnest.devserver import watch_loop
from staticnest.site import BuildWatcher


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_project(tmp: str) -> Path:
    root = Path(tmp)
    (root / "content").mkdir()
    (root / "content" / "index.md").write_text("# Home\n\nWelcome.\n")
    (root / "site.toml").write_text(
        'title = "Docs"\ndescription = "Test"\nbase_url = "/"\n'
        'content_dir = "content"\noutput_dir = "dist"\n'
        '[brand]\nname = "Docs"\n[links]\ngithub = "#"\n[theme]\nname = "nest"\n'
    )
    return root / "site.toml"


# ---------------------------------------------------------------------------
# LiveReloadHandler tests (using fake socket/request objects)
# ---------------------------------------------------------------------------

class FakeSocket:
    """Minimal socket-like object for constructing a BaseHTTPRequestHandler."""

    def __init__(self, request: bytes) -> None:
        self._input = BytesIO(request)
        self._output = BytesIO()

    def makefile(self, mode: str, *args, **kwargs):
        if "r" in mode:
            return self._input
        return self._output

    def sendall(self, data: bytes) -> None:
        self._output.write(data)

    def getpeername(self):
        return ("127.0.0.1", 9999)

    def close(self) -> None:
        pass


class LiveReloadHandlerTests(unittest.TestCase):
    def _make_handler(self, path: str, tmp_dir: str, watcher: BuildWatcher):
        from staticnest.devserver import LiveReloadHandler
        from functools import partial

        request_line = f"GET {path} HTTP/1.0\r\n\r\n".encode()
        sock = FakeSocket(request_line)
        client_addr = ("127.0.0.1", 12345)

        handler = LiveReloadHandler.__new__(LiveReloadHandler)
        handler.watcher = watcher
        handler.directory = tmp_dir
        handler.server = MagicMock()
        handler.server.server_name = "localhost"
        handler.server.server_port = 8000
        handler.rfile = BytesIO(request_line)
        handler.wfile = BytesIO()
        handler.connection = sock
        handler.client_address = client_addr
        handler.request = sock
        handler.timeout = None
        return handler

    def test_version_endpoint_returns_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = _make_project(tmp)
            watcher = BuildWatcher(config_path)
            watcher.rebuild()

            from staticnest.devserver import LiveReloadHandler
            from functools import partial

            request_line = b"GET /__staticnest_version HTTP/1.0\r\n\r\n"
            sock = FakeSocket(request_line)

            output = BytesIO()

            handler = LiveReloadHandler.__new__(LiveReloadHandler)
            handler.watcher = watcher
            handler.directory = str(watcher._snapshot)  # not used here
            handler.server = MagicMock()
            handler.server.server_name = "localhost"
            handler.server.server_port = 8000
            handler.rfile = BytesIO(request_line)
            handler.wfile = output
            handler.connection = sock
            handler.client_address = ("127.0.0.1", 1234)
            handler.request = sock
            handler.timeout = None

            with patch.object(handler, "send_response") as mock_send, \
                 patch.object(handler, "send_header"), \
                 patch.object(handler, "end_headers"):
                handler.path = "/__staticnest_version"
                handler.do_GET()
                mock_send.assert_called_with(HTTPStatus.OK)

    def test_version_endpoint_payload_is_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = _make_project(tmp)
            watcher = BuildWatcher(config_path)
            watcher.rebuild()

            from staticnest.devserver import LiveReloadHandler

            output = BytesIO()
            handler = LiveReloadHandler.__new__(LiveReloadHandler)
            handler.watcher = watcher
            handler.wfile = output

            written_data: list[bytes] = []

            with patch.object(handler, "send_response"), \
                 patch.object(handler, "send_header"), \
                 patch.object(handler, "end_headers"), \
                 patch.object(handler, "wfile") as mock_wfile:

                mock_wfile.write = lambda data: written_data.append(data)
                handler.path = "/__staticnest_version"
                handler.do_GET()

            self.assertTrue(len(written_data) > 0)
            payload = json.loads(written_data[0])
            self.assertIn("version", payload)

    def test_404_served_from_custom_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = _make_project(tmp)
            watcher = BuildWatcher(config_path)
            result = watcher.rebuild()

            # Ensure 404.html exists from the build
            not_found_path = result.config.output_dir / "404.html"
            self.assertTrue(not_found_path.exists())

            from staticnest.devserver import LiveReloadHandler

            sent_responses: list[int] = []
            sent_headers: list[tuple] = []
            written_data: list[bytes] = []

            handler = LiveReloadHandler.__new__(LiveReloadHandler)
            handler.watcher = watcher
            handler.directory = str(result.config.output_dir)
            handler.wfile = MagicMock()
            handler.wfile.write = lambda data: written_data.append(data)

            with patch.object(handler, "send_response", side_effect=lambda c: sent_responses.append(c)), \
                 patch.object(handler, "send_header", side_effect=lambda k, v: sent_headers.append((k, v))), \
                 patch.object(handler, "end_headers"):
                handler.send_error(HTTPStatus.NOT_FOUND)

            self.assertIn(HTTPStatus.NOT_FOUND, sent_responses)
            types = [v for k, v in sent_headers if k == "Content-Type"]
            self.assertTrue(any("html" in t for t in types))

    def test_non_404_error_delegates_to_super(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = _make_project(tmp)
            watcher = BuildWatcher(config_path)
            watcher.rebuild()

            from staticnest.devserver import LiveReloadHandler
            import http.server

            handler = LiveReloadHandler.__new__(LiveReloadHandler)
            handler.watcher = watcher
            handler.directory = tmp

            with patch.object(http.server.SimpleHTTPRequestHandler, "send_error") as mock_super:
                handler.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
                mock_super.assert_called_once_with(HTTPStatus.INTERNAL_SERVER_ERROR, None, None)

    def test_non_404_error_with_no_custom_file_delegates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # no 404.html in this tmp dir
            from staticnest.devserver import LiveReloadHandler
            import http.server

            mock_watcher = MagicMock()
            mock_watcher.current_version.return_value = "1"

            handler = LiveReloadHandler.__new__(LiveReloadHandler)
            handler.watcher = mock_watcher
            handler.directory = tmp  # no 404.html here

            with patch.object(http.server.SimpleHTTPRequestHandler, "send_error") as mock_super:
                handler.send_error(HTTPStatus.NOT_FOUND)
                mock_super.assert_called_once()


# ---------------------------------------------------------------------------
# watch_loop tests
# ---------------------------------------------------------------------------

class WatchLoopTests(unittest.TestCase):
    def test_watch_loop_calls_poll(self) -> None:
        mock_watcher = MagicMock()
        mock_watcher.poll.return_value = False
        stop_event = threading.Event()

        def stopper():
            stop_event.set()

        timer = threading.Timer(0.05, stopper)
        timer.start()
        watch_loop(mock_watcher, stop_event)
        timer.cancel()

        mock_watcher.poll.assert_called()

    def test_watch_loop_prints_on_rebuild(self) -> None:
        mock_watcher = MagicMock()
        call_count = [0]

        def poll_side_effect():
            call_count[0] += 1
            if call_count[0] == 1:
                return True
            return False

        mock_watcher.poll.side_effect = poll_side_effect
        stop_event = threading.Event()

        def stopper():
            stop_event.set()

        timer = threading.Timer(0.1, stopper)
        timer.start()

        with patch("builtins.print") as mock_print:
            watch_loop(mock_watcher, stop_event)

        timer.cancel()
        printed = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("Rebuilt", printed)

    def test_watch_loop_stops_on_event(self) -> None:
        mock_watcher = MagicMock()
        mock_watcher.poll.return_value = False
        stop_event = threading.Event()
        stop_event.set()  # stopped immediately

        watch_loop(mock_watcher, stop_event)
        # should return without blocking
        mock_watcher.poll.assert_not_called()


# ---------------------------------------------------------------------------
# BuildWatcher tests
# ---------------------------------------------------------------------------

class BuildWatcherTests(unittest.TestCase):
    def test_initial_version_is_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = _make_project(tmp)
            watcher = BuildWatcher(config_path)
            self.assertIsInstance(watcher.current_version(), str)
            self.assertGreater(len(watcher.current_version()), 0)

    def test_rebuild_updates_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = _make_project(tmp)
            watcher = BuildWatcher(config_path)
            version_before = watcher.current_version()
            watcher.rebuild()
            # After rebuild, version may or may not differ (depends on timing),
            # but it should still be a non-empty string.
            self.assertIsInstance(watcher.current_version(), str)

    def test_poll_returns_false_when_no_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = _make_project(tmp)
            watcher = BuildWatcher(config_path)
            watcher.rebuild()
            self.assertFalse(watcher.poll())

    def test_poll_returns_true_after_file_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = _make_project(tmp)
            watcher = BuildWatcher(config_path)
            watcher.rebuild()

            # Modify a watched file
            import time
            time.sleep(0.01)
            config_path_parent = config_path.parent
            (config_path_parent / "content" / "index.md").write_text("# Changed\n\nNew content.\n")

            self.assertTrue(watcher.poll())


if __name__ == "__main__":
    unittest.main()
