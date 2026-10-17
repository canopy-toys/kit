"""The kit's failing-check switch: fail on a pull request whose branch matches the variable TOY_FAIL_BRANCH.

The reset script points TOY_FAIL_BRANCH at one ticket's branches (space-separated globs), so that ticket's PR fails CI
whatever is pushed to it. Unset or "none", every branch passes.
"""

import fnmatch
import os
import sys

branch = os.environ.get("GITHUB_HEAD_REF", "")
patterns = os.environ.get("TOY_FAIL_BRANCH", "").split()
if branch and any(fnmatch.fnmatch(branch, p) for p in patterns):
    print(f"{branch}: integration check failed", file=sys.stderr)
    sys.exit(1)
print("integration check passed")
