---
title: Add a `pow` subcommand
scenario: S8
---
Add a `pow` subcommand: `calc pow 2 10` prints `1024`. It takes the same two arguments as the other operations and
honors `--precision`.

Add a test for it in `tests/test_ops.py` and one in `tests/test_cli.py`, and a line under Unreleased in
`CHANGELOG.md`.
