"""The command line's contract. Scripts depend on these exit codes: change them only with a CHANGELOG entry."""

import contextlib
import io
import unittest

from calc.cli import main


def run(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = main(list(argv))
        except SystemExit as e:
            code = int(e.code or 0)
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    def test_add(self) -> None:
        self.assertEqual(run("add", "2", "3"), (0, "5\n", ""))

    def test_precision(self) -> None:
        self.assertEqual(run("--precision", "2", "div", "1", "3"), (0, "0.33\n", ""))

    def test_not_a_number_exits_1(self) -> None:
        code, _, err = run("add", "two", "3")
        self.assertEqual(code, 1)
        self.assertIn("not a number", err)

    def test_runtime_errors_exit_1(self) -> None:
        """Every error after the arguments parse exits 1: division by zero is one."""
        code, _, err = run("div", "1", "0")
        self.assertEqual(code, 1)
        self.assertIn("division by zero", err)

    def test_bad_usage_exits_2(self) -> None:
        code, _, _ = run("frobnicate", "1", "2")
        self.assertEqual(code, 2)
