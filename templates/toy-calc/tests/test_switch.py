"""The kit's failing-check switch: CI fails while `ci/must_fail` exists. The kit's scripts commit it to a branch."""

import pathlib
import unittest

MARKER = pathlib.Path(__file__).resolve().parent.parent / "ci" / "must_fail"


class SwitchTest(unittest.TestCase):
    def test_must_fail_marker_absent(self) -> None:
        self.assertFalse(MARKER.exists(), f"{MARKER.name} is present: this branch is meant to fail CI")
