---
title: Make division by zero exit 2
scenario: S9
fail_ci: true
---
`calc div 1 0` exits 1. Make it exit 2, so a script can tell division by zero apart from a bad number.

Update the test in `tests/test_cli.py` and add a line under Unreleased in `CHANGELOG.md`: scripts depend on the exit
codes.
