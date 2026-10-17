#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""Set up and reset the canopy toy repositories, with the operator's own admin `gh`.

    ./toys.py setup toy-calc     create the repository if needed, seed it once, and apply its settings
    ./toys.py reset toy-calc     back to the seed: PRs closed, agent/ branches gone, main forced, catalog recreated
    ./toys.py reset all

Standard library only. Every GitHub call goes through `gh`.
"""

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

KIT = pathlib.Path(__file__).resolve().parent
CONFIG = tomllib.loads((KIT / "kit.toml").read_text())
ORG: str = CONFIG["org"]
RULESET = "main"
SEED_TAG = "seed"
BRANCH_PREFIX = "agent/"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["setup", "reset"])
    parser.add_argument("repo", help="a toy repository, such as toy-calc, or all")
    args = parser.parse_args()
    repos = toy_repos() if args.repo == "all" else [args.repo]
    for repo in repos:
        if repo not in toy_repos():
            sys.exit(f"no template for {repo}: expected one of {', '.join(toy_repos())}")
        if args.command == "setup":
            setup(repo)
        else:
            reset(repo)
    return 0


def toy_repos() -> list[str]:
    return sorted(p.name for p in (KIT / "templates").iterdir() if p.is_dir() and p.name != "common")


def setup(repo: str) -> None:
    """Create and seed the repository if it is new, then apply every setting. Safe to run again."""
    full = f"{ORG}/{repo}"
    if gh("repo", "view", full, "--json", "name", check=False) is None:
        log(f"{full}: creating")
        gh("repo", "create", full, "--public", "--description", f"A toy repository for testing canopy: {repo}")
    if gh_api(f"repos/{full}/git/ref/tags/{SEED_TAG}", check=False) is None:
        seed(repo)
    configure(repo)


def reset(repo: str) -> None:
    """Return the repository to its seed, recreate its catalog, and print each scenario's new issue."""
    full = f"{ORG}/{repo}"
    configure(repo)
    for pr in json.loads(gh("pr", "list", "-R", full, "--state", "open", "--json", "number", "--limit", "500")):
        log(f"{full}: closing PR #{pr['number']}")
        gh("pr", "close", str(pr["number"]), "-R", full, "--delete-branch", check=False)
    refs = gh_api(f"repos/{full}/git/matching-refs/heads/{BRANCH_PREFIX}", paginate=True) or []
    for ref in refs:
        log(f"{full}: deleting {ref['ref']}")
        gh_api(f"repos/{full}/git/{ref['ref']}", method="DELETE", check=False)
    seed_sha = gh_api(f"repos/{full}/git/ref/tags/{SEED_TAG}")["object"]["sha"]
    with ruleset_disabled(full):
        log(f"{full}: forcing main to {SEED_TAG} ({seed_sha[:8]})")
        gh_api(f"repos/{full}/git/refs/heads/main", method="PATCH", fields={"sha": seed_sha, "force": True})
    for issue in json.loads(gh("issue", "list", "-R", full, "--state", "open", "--json", "number", "--limit", "500")):
        gh("issue", "close", str(issue["number"]), "-R", full, "--reason", "not planned")
    create_catalog(repo)


@dataclass
class CatalogIssue:
    slug: str
    title: str
    scenario: str
    body: str
    autolabel: bool = False
    blocked_by: list[str] = field(default_factory=list)


def create_catalog(repo: str) -> None:
    full = f"{ORG}/{repo}"
    numbers: dict[str, int] = {}
    ids: dict[str, int] = {}
    for item in read_catalog(repo):
        body = item.body
        missing = [slug for slug in item.blocked_by if slug not in numbers]
        if missing:
            sys.exit(f"{item.slug}: blocked by {', '.join(missing)}, which is not earlier in the catalog")
        if item.blocked_by:
            body += "\n\n" + "\n".join(f"Blocked by #{numbers[slug]}" for slug in item.blocked_by)
        fields: dict[str, object] = {"title": item.title, "body": body}
        if item.autolabel:
            fields["labels[]"] = CONFIG["queue_label"]
        created = gh_api(f"repos/{full}/issues", method="POST", fields=fields)
        numbers[item.slug], ids[item.slug] = created["number"], created["id"]
        for slug in item.blocked_by:
            # GitHub's own issue dependency, beside the body line, in case the tracker reads only one of them.
            if gh_api(
                f"repos/{full}/issues/{created['number']}/dependencies/blocked_by",
                method="POST",
                fields={"issue_id": ids[slug]},
                check=False,
            ) is None:
                log(f"{full}: could not add GitHub's blocked-by dependency; the body line stands alone")
        print(f"{item.scenario:<24} {repo:<10} GH-{created['number']:<4} {item.title}")


def read_catalog(repo: str) -> list[CatalogIssue]:
    items = []
    for path in sorted((KIT / "issues" / repo).glob("*.md")):
        _, front, body = path.read_text().split("---\n", 2)
        meta = dict(line.split(":", 1) for line in front.strip().splitlines())
        meta = {k.strip(): v.strip() for k, v in meta.items()}
        blocked = [s.strip() for s in meta.get("blocked_by", "").split(",") if s.strip()]
        items.append(
            CatalogIssue(
                slug=path.stem,
                title=meta["title"],
                scenario=meta["scenario"],
                body=body.strip(),
                autolabel=meta.get("autolabel", "false") == "true",
                blocked_by=blocked,
            )
        )
    return items


def seed(repo: str) -> None:
    """Push the template as main's first commit and tag it `seed`."""
    full = f"{ORG}/{repo}"
    log(f"{full}: seeding")
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        shutil.copytree(KIT / "templates" / "common", work, dirs_exist_ok=True)
        shutil.copytree(KIT / "templates" / repo, work, dirs_exist_ok=True)
        url = f"https://github.com/{full}.git"
        for args in (
            ["init", "-q", "-b", "main"],
            ["add", "-A"],
            ["commit", "-q", "-m", "Seed"],
            ["tag", SEED_TAG],
            ["push", "-q", url, "main", f"refs/tags/{SEED_TAG}"],
        ):
            # gh's credential helper for this push only, leaving the operator's git config alone.
            helper = ["-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential"]
            subprocess.run(["git", "-C", str(work), *helper, *args], check=True)


def configure(repo: str) -> None:
    """Apply the repository's settings, labels, and ruleset. The same on setup and every reset."""
    full = f"{ORG}/{repo}"
    log(f"{full}: applying settings")
    gh(
        "repo", "edit", full,
        "--enable-issues", "--enable-wiki=false", "--enable-projects=false", "--delete-branch-on-merge",
    )  # fmt: skip
    gh_api(
        f"repos/{full}/actions/permissions/workflow",
        method="PUT",
        fields={"default_workflow_permissions": "read", "can_approve_pull_request_reviews": True},
    )
    gh_api(
        f"repos/{full}/actions/permissions/fork-pr-contributor-approval",
        method="PUT",
        fields={"approval_policy": "all_external_contributors"},
    )
    gh("variable", "set", "TOY_FETCH_URL", "-R", full, "--body", CONFIG["fetch_url"])
    for name, color, description in (
        (CONFIG["queue_label"], "0e8a16", "The toy queue: canopy may start this"),
        (CONFIG["needs_human_label"], "d93f0b", "Waiting on a person"),
        (CONFIG["pr_label"], "5319e7", "Opened by canopy"),
    ):
        gh("label", "create", name, "-R", full, "--color", color, "--description", description, "--force")
    ruleset = {
        "name": RULESET,
        "target": "branch",
        "enforcement": "active",
        "bypass_actors": [],
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {
                "type": "pull_request",
                "parameters": {
                    "required_approving_review_count": 1,
                    "dismiss_stale_reviews_on_push": False,
                    "require_code_owner_review": False,
                    "require_last_push_approval": False,
                    "required_review_thread_resolution": False,
                },
            },
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": False,
                    "required_status_checks": [{"context": "check"}],
                },
            },
        ],
    }
    existing = ruleset_id(full)
    if existing is None:
        gh_api(f"repos/{full}/rulesets", method="POST", body=ruleset)
    else:
        gh_api(f"repos/{full}/rulesets/{existing}", method="PUT", body=ruleset)


@contextmanager
def ruleset_disabled(full: str) -> Iterator[None]:
    """Disable main's ruleset for the block, and re-enable it however the block ends."""
    rid = ruleset_id(full)
    if rid is None:
        sys.exit(f"{full}: no {RULESET} ruleset; run setup first")
    gh_api(f"repos/{full}/rulesets/{rid}", method="PUT", body={"enforcement": "disabled"})
    try:
        yield
    finally:
        gh_api(f"repos/{full}/rulesets/{rid}", method="PUT", body={"enforcement": "active"})
        log(f"{full}: ruleset active again")


def ruleset_id(full: str) -> int | None:
    for ruleset in gh_api(f"repos/{full}/rulesets") or []:
        if ruleset["name"] == RULESET:
            return ruleset["id"]
    return None


def gh_api(
    path: str,
    *,
    method: str = "GET",
    fields: dict[str, object] | None = None,
    body: object = None,
    paginate: bool = False,
    check: bool = True,
):  # noqa: ANN201 - the parsed JSON response
    args = ["api", path, "-X", method]
    if paginate:
        args += ["--paginate", "--slurp"]
    for key, value in (fields or {}).items():
        # -F types booleans and numbers; -f keeps strings strings.
        if isinstance(value, bool | int):
            args += ["-F", f"{key}={str(value).lower()}"]
        else:
            args += ["-f", f"{key}={value}"]
    out = gh(*args, input=None if body is None else json.dumps(body), check=check)
    if out is None or not out.strip():
        return None
    data = json.loads(out)
    if paginate:
        data = [item for page in data for item in (page if isinstance(page, list) else [page])]
    return data


def gh(*args: str, input: str | None = None, check: bool = True) -> str | None:
    """Run gh and return its stdout, or None when it fails and `check` is off."""
    if input is not None:
        args = (*args, "--input", "-")
    result = subprocess.run(["gh", *args], input=input, capture_output=True, text=True)
    if result.returncode != 0:
        if check:
            sys.exit(f"gh {' '.join(args)} failed:\n{result.stderr.strip()}")
        return None
    return result.stdout


def log(message: str) -> None:
    print(message, file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
