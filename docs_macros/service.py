"""Own a temporary local sparqld process for catalog queries."""

import json
import os
import socket
import tempfile
import time
from contextlib import ExitStack, contextmanager
from urllib.request import Request, urlopen

import sh

STARTUP_TIMEOUT = 30
POLL_TIMEOUT = 0.25


@contextmanager
def _devnull():
    with open(os.devnull, "wb") as discarded:
        yield discarded


class CatalogService:
    """Load one docs directory with a process owned by this operation."""

    def __init__(self, directory):
        self.directory = directory

    def __enter__(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        self.endpoint = f"http://127.0.0.1:{port}/"
        self.resources = ExitStack()
        self.errors = self.resources.enter_context(
            tempfile.TemporaryFile(mode="w+", encoding="utf-8")
        )
        self.discarded = self.resources.enter_context(_devnull())
        self.process = sh.sparqld(
            str(self.directory),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--no-watch",
            _bg=True,
            _bg_exc=False,
            _out=self.discarded,
            _err=self.errors,
        )
        try:
            self._wait()
        except Exception:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, *exception):
        self._stop()
        self.resources.close()

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
            if not self.process.is_alive():
                self.errors.seek(0)
                raise RuntimeError(self.errors.read())
            try:
                with urlopen(self.endpoint, timeout=POLL_TIMEOUT):
                    return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("Timed out loading the example catalog")

    def _stop(self):
        if self.process.is_alive():
            self.process.process.terminate()
        try:
            self.process.wait(timeout=5)
        except sh.TimeoutException:
            self.process.process.kill()
            self._reap()
        except sh.SignalException:
            return

    def _reap(self):
        try:
            self.process.wait()
        except sh.SignalException:
            return
