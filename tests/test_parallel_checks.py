"""Verify concurrent checks finish and preserve failures."""

import sys
import unittest
from functools import partial
from threading import Barrier, Event

from project_checks.commands import run_command, run_parallel

CHECK_TIMEOUT = 5
FAILURE_STATUS = 101


def _check(barrier, status):
    barrier.wait(timeout=CHECK_TIMEOUT)
    return status


def _raise_check(barrier):
    barrier.wait(timeout=CHECK_TIMEOUT)
    raise ValueError("check failed")


def _finish_check(barrier, finished):
    barrier.wait(timeout=CHECK_TIMEOUT)
    finished.set()
    return 0


class ParallelCheckTests(unittest.TestCase):
    def test_checks_overlap_and_preserve_failure(self):
        barrier = Barrier(2)
        status = run_parallel(
            partial(_check, barrier, 0), partial(_check, barrier, FAILURE_STATUS)
        )
        self.assertEqual(status, FAILURE_STATUS)

    def test_exception_waits_for_other_check(self):
        barrier = Barrier(2)
        finished = Event()
        with self.assertRaisesRegex(ValueError, "check failed"):
            run_parallel(
                partial(_raise_check, barrier),
                partial(_finish_check, barrier, finished),
            )
        self.assertTrue(finished.is_set())

    def test_command_preserves_cargo_failure_status(self):
        status = run_command(
            sys.executable, "-c", f"raise SystemExit({FAILURE_STATUS})"
        )
        self.assertEqual(status, FAILURE_STATUS)
