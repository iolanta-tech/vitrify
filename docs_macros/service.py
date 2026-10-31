"""Own a temporary local sparqld process for catalog queries."""

import json
import socket
import subprocess
import tempfile
import time
from urllib.request import Request, urlopen


STARTUP_TIMEOUT = 30
POLL_TIMEOUT = 0.25


class CatalogService:
    """Load one docs directory with a process owned by this operation."""

    def __init__(self, directory):
        self.directory = directory

    def __enter__(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        self.endpoint = f"http://127.0.0.1:{port}/"
        self.errors = tempfile.TemporaryFile()
        self.process = subprocess.Popen(
            [
                "sparqld",
                str(self.directory),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--no-watch",
            ],
            stdout=subprocess.DEVNULL,
            stderr=self.errors,
        )
        try:
            self._wait()
        except Exception:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, *exception):
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.errors.close()

    def query(self, query):
        request = Request(
            self.endpoint,
            data=query.encode("utf-8"),
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
        )
        with urlopen(request, timeout=STARTUP_TIMEOUT) as response:
            return json.load(response)["results"]["bindings"]

    def _wait(self):
        deadline = time.monotonic() + STARTUP_TIMEOUT
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                self.errors.seek(0)
                raise RuntimeError(self.errors.read().decode("utf-8"))
            try:
                with urlopen(self.endpoint, timeout=POLL_TIMEOUT):
                    return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("Timed out loading the example catalog")
