---
title: Add rounding modes
scenario: S11
---
Add a `--rounding` option that picks how `--precision` rounds: half-even (what Python's `round` does now), half-up,
or toward zero.

Before you start, ask on this issue which mode should be the default, and wait for the answer. Changing the default
changes output scripts already depend on.
