---
title: Use `parse_number` in the CLI
scenario: S12
blocked_by: 05-parse-module
---
Use `calc.parse.parse_number` in `calc/cli.py` in place of `float`, so `calc add 1/4 1/4` prints `0.5`. Add a test to
`tests/test_cli.py` and a line under Unreleased in `CHANGELOG.md`.
