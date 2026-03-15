from __future__ import annotations

from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time

from staticnest.site import BuildWatcher


class LiveReloadHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str, watcher: BuildWatcher, **kwargs) -> None:
        self.watcher = watcher
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self) -> None:
        if self.path == "/__staticnest_version":
            payload = json.dumps({"version": self.watcher.current_version()}).encode()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        super().do_GET()

    def send_error(
        self,
        code: int,
        message: str | None = None,
        explain: str | None = None,
    ) -> None:
        if code != HTTPStatus.NOT_FOUND:
            super().send_error(code, message, explain)
            return

        not_found_path = Path(self.directory) / "404.html"
        if not not_found_path.exists():
            super().send_error(code, message, explain)
            return

        payload = not_found_path.read_bytes()
        self.send_response(HTTPStatus.NOT_FOUND)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def watch_loop(watcher: BuildWatcher, stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        try:
            if watcher.poll():
                print("Rebuilt site after file change")
        except Exception as exc:  # pragma: no cover - dev feedback path
            print(f"Build failed: {exc}")
        stop_event.wait(0.8)


def serve_site(config_path: Path, host: str, port: int) -> None:
    watcher = BuildWatcher(config_path)
    result = watcher.rebuild()
    stop_event = threading.Event()
    watcher_thread = threading.Thread(target=watch_loop, args=(watcher, stop_event), daemon=True)
    watcher_thread.start()

    handler = partial(
        LiveReloadHandler,
        directory=str(result.config.output_dir),
        watcher=watcher,
    )
    server = ThreadingHTTPServer((host, port), handler)

    print(f"Serving {result.config.output_dir} at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        server.server_close()
