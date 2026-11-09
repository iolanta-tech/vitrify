"""Shared setup and recorded stand-ins for pytest."""

import re


def search(pattern, text):
    return re.search(pattern, text)


class Fixture:
    """Run cleanups after each test, in reverse order of registration."""

    def setup_method(self):
        self._cleanups = []

    def add_cleanup(self, function, *arguments):
        self._cleanups.append((function, arguments))

    def teardown_method(self):
        while self._cleanups:
            function, arguments = self._cleanups.pop()
            function(*arguments)


class RecordedCall:
    """Stand in for a function and remember how it was called."""

    def __init__(self, returned):
        self.returned = returned
        self.call_count = 0
        self.arguments = ()
        self.keywords = {}

    def __call__(self, *arguments, **keywords):
        self.call_count += 1
        self.arguments = arguments
        self.keywords = keywords
        return self.returned
