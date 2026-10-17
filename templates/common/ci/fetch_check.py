"""The kit's staged-outage switch: fail when the repository variable TOY_FETCH_URL cannot be fetched.

Point TOY_FETCH_URL at an unreachable host to stage a CI outage, and back to a reachable one to end it. Unset, the
check passes.
"""

import os
import sys
import urllib.request

url = os.environ.get("TOY_FETCH_URL", "")
if not url:
    print("TOY_FETCH_URL is unset: nothing to fetch")
    sys.exit(0)
try:
    with urllib.request.urlopen(url, timeout=10) as response:
        print(f"fetched {url}: {response.status}")
except OSError as e:
    print(f"could not fetch {url}: {e}", file=sys.stderr)
    sys.exit(1)
