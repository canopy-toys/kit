---
title: Add a `parse` module for numbers
scenario: S12
---
Add `calc/parse.py` with `parse_number(text: str) -> float`. It accepts what `float` does, plus a fraction written
`a/b` (`1/4` is `0.25`), and raises `ValueError` with a clear message for anything else, a zero denominator included.

Test it in a new `tests/test_parse.py`. Do not use it in the CLI yet: that is a separate issue.
