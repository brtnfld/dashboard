#!/usr/bin/env python3
"""Validate a "Register a project" issue and, if well-formed, write
registry/<owner>_<repo>.yaml. Called from
.github/workflows/register-project.yml, which handles the GitHub-side
orchestration (posting comments, opening/merging the PR) via `gh`.

Reads the raw issue body from stdin. Requires env vars ISSUE_AUTHOR and
(for anything beyond anonymous rate limits) GITHUB_TOKEN.

Always exits 0 and prints one JSON object to stdout -- this script's job is
to produce a checklist, not to fail the workflow:
  {
    "valid": bool,       # a registry file was written
    "auto_merge": bool,  # trusted submitter + every check (hard + soft) passed
    "repo": "Owner/repo" or null,
    "file_path": "registry/Owner_repo.yaml" or null,
    "checklist": [{"label": str, "passed": bool, "detail": str}, ...],
  }
"""

import base64
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_DIR = ROOT / "registry"
POLICY_FILE = REGISTRY_DIR / "policy.yaml"
CODEOWNERS_FILE = ROOT / ".github" / "CODEOWNERS"
NON_ENTRY_FILES = {"TEMPLATE.yaml", "policy.yaml"}

# Must match catalog/category_info.json (this dashboard's own catalog
# categories -- not the CASS software-catalog's areas vocabulary).
VALID_AREAS = {
    "DATA AND VISUALIZATION",
    "DEVELOPMENT TOOLS",
    "MATHEMATICAL LIBRARIES",
    "PROGRAMMING MODELS AND RUNTIMES",
    "SOFTWARE ECOSYSTEM AND DELIVERY",
}

# Must match PROJECT_CONFIG_PATH in corsa-center/metrics' orchestrator.py.
PROJECT_CONFIG_PATH = ".corsa/metrics.yaml"


def parse_issue_form(body: str) -> dict:
    """Split a GitHub issue-form body into {label: value} by '### ' headings.

    A `type: markdown` block in the form (like the ownership-proof reminder
    in register-project.yml) never appears in the submitted body -- only
    actual field labels do -- so splitting from the first '### ' is safe.
    """
    fields = {}
    for block in re.split(r"^### ", body, flags=re.MULTILINE)[1:]:
        heading, _, rest = block.partition("\n")
        value = rest.strip()
        if value == "_No response_":
            value = ""
        fields[heading.strip()] = value
    return fields


def gh_get(path: str, token: str = None):
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return requests.get(f"https://api.github.com{path}", headers=headers, timeout=30)


def check_repo(repo_slug: str, token: str):
    """Returns (ok, canonical_full_name_or_None, detail, repo_json_or_None)."""
    resp = gh_get(f"/repos/{repo_slug}", token)
    if resp.status_code != 200:
        return False, None, f"GitHub repo {repo_slug} not found or inaccessible (HTTP {resp.status_code})", None
    data = resp.json()
    if data.get("private"):
        return False, None, f"{repo_slug} is private", None
    if data.get("archived"):
        return False, None, f"{repo_slug} is archived", None
    return True, data["full_name"], f"{data['full_name']} exists, public, not archived", data


def check_ownership(canonical_repo: str, declared_repo: str, token: str):
    """Verify canonical_repo's own .corsa/metrics.yaml names itself.

    Proof that *someone* with merge authority over the repo endorsed this
    registration -- but not proof that the filer is that someone. See
    check_contributor() for the check tying it to the filer specifically.
    """
    resp = gh_get(f"/repos/{canonical_repo}/contents/{PROJECT_CONFIG_PATH}", token)
    if resp.status_code != 200:
        return False, f"{PROJECT_CONFIG_PATH} not found in {canonical_repo}"
    content = base64.b64decode(resp.json().get("content", "")).decode("utf-8", "replace")
    match = re.search(r"^repo:\s*(.+?)\s*$", content, re.MULTILINE)
    if not match:
        return False, f"{PROJECT_CONFIG_PATH} has no 'repo:' field"
    declared_in_file = match.group(1).strip().strip("\"'")
    if declared_in_file.lower() != declared_repo.lower():
        return False, f"{PROJECT_CONFIG_PATH} declares repo: {declared_in_file!r}, expected {declared_repo!r}"
    return True, f"{PROJECT_CONFIG_PATH} present and matches"


def check_contributor(canonical_repo: str, username: str, token: str):
    """Whether `username` appears in canonical_repo's contributor history.

    Ties the registration to the filer specifically: check_ownership() only
    proves someone had authority over the repo at some point, so without
    this, anyone could file (and, if trusted, auto-merge) a registration for
    a project once PROJECT_CONFIG_PATH exists, regardless of their own
    relationship to it. This alone doesn't gate `valid` -- an unaffiliated
    filer still gets a real PR, just not auto-merge; see main().

    Returns ("pass"|"fail"|"inconclusive", detail). GitHub refuses to
    compute the contributor list for repos with very large histories (HTTP
    403 -- confirmed on torvalds/linux); that's inconclusive, not evidence
    against the filer, and is treated as passing for auto-merge purposes.
    Only checks the first page (up to 100, by commit count) -- a legitimate
    contributor further down the list fails this specific check, same as
    inconclusive: no auto-merge, but the PR still opens.
    """
    resp = gh_get(f"/repos/{canonical_repo}/contributors?per_page=100", token)
    if resp.status_code != 200:
        return "inconclusive", f"could not fetch contributors for {canonical_repo} (HTTP {resp.status_code})"
    logins = {c.get("login", "").lower() for c in resp.json() if isinstance(c, dict)}
    if username.lower() in logins:
        return "pass", f"{username} has committed to {canonical_repo}"
    return "fail", f"{username} not found among {canonical_repo}'s top 100 contributors by commits"


def check_areas(areas_raw: str):
    areas = [a.strip() for a in areas_raw.split(",") if a.strip()]
    if not areas:
        return False, [], "no category selected"
    invalid = [a for a in areas if a not in VALID_AREAS]
    if invalid:
        return False, areas, f"invalid categor{'y' if len(invalid) == 1 else 'ies'}: {invalid}"
    return True, areas, "valid"


def check_collision(bare_name: str, exclude_file: str = None):
    for path in REGISTRY_DIR.glob("*.yaml"):
        if path.name in NON_ENTRY_FILES or path.name == exclude_file:
            continue
        if path.stem.split("_", 1)[-1].lower() == bare_name.lower():
            return False, f"bare name {bare_name!r} collides with existing {path.name}"
    return True, "no collision with an existing registry entry"


def load_policy():
    if POLICY_FILE.exists():
        with open(POLICY_FILE) as f:
            return yaml.safe_load(f) or {}
    return {}


def check_soft_gates(repo_json: dict, submitter: str, policy: dict):
    """Auto-merge eligibility heuristics. Never a hard rejection -- see module
    docstring; a failing check here only costs auto-merge, not the PR itself.
    """
    checks = []

    min_age_days = policy.get("min_repo_age_days", 0)
    created_at = datetime.fromisoformat(repo_json["created_at"].replace("Z", "+00:00"))
    age_days = (datetime.now(timezone.utc) - created_at).days
    checks.append(("repo age", age_days >= min_age_days, f"{age_days}d old, need >= {min_age_days}d"))

    min_stars = policy.get("min_stars", 0)
    stars = repo_json.get("stargazers_count", 0)
    checks.append(("stars", stars >= min_stars, f"{stars} stars, need >= {min_stars}"))

    max_per_day = policy.get("max_auto_merges_per_submitter_per_day", 3)
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    recent = 0
    for path in REGISTRY_DIR.glob("*.yaml"):
        if path.name in NON_ENTRY_FILES:
            continue
        try:
            data = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError:
            continue
        if data.get("submitted_by") != submitter or not data.get("registered_at"):
            continue
        try:
            when = datetime.fromisoformat(str(data["registered_at"]).replace("Z", "+00:00"))
        except ValueError:
            continue
        if when >= cutoff:
            recent += 1
    checks.append(("submitter rate limit", recent < max_per_day, f"{recent} in last 24h, limit {max_per_day}"))

    return all(passed for _, passed, _ in checks), checks


def check_trust(submitter: str, token: str):
    """Whether `submitter` is a CODEOWNERS owner for a registry/** pattern."""
    if not CODEOWNERS_FILE.exists():
        return False, "no CODEOWNERS file"
    for line in CODEOWNERS_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if not parts or not parts[0].startswith("registry/"):
            continue
        for owner in parts[1:]:
            owner = owner.lstrip("@")
            if "/" in owner:
                org, team = owner.split("/", 1)
                resp = gh_get(f"/orgs/{org}/teams/{team}/memberships/{submitter}", token)
                if resp.status_code == 200 and resp.json().get("state") == "active":
                    return True, f"member of @{owner}"
            elif owner.lower() == submitter.lower():
                return True, f"listed as @{owner}"
    return False, "not listed in CODEOWNERS for a registry/** pattern"


def main():
    body = sys.stdin.read()
    submitter = os.environ["ISSUE_AUTHOR"]
    token = os.environ.get("GITHUB_TOKEN")

    fields = parse_issue_form(body)
    checklist = []
    result = {"valid": False, "auto_merge": False, "repo": None, "file_path": None}

    def finish():
        result["checklist"] = checklist
        print(json.dumps(result))

    repo_slug = fields.get("GitHub repository", "").strip()
    if not re.match(r"^[\w.-]+/[\w.-]+$", repo_slug):
        checklist.append({"label": "repo format", "passed": False, "detail": f"{repo_slug!r} is not owner/repo"})
        return finish()

    ok, canonical_repo, detail, repo_json = check_repo(repo_slug, token)
    checklist.append({"label": "repo exists/public/not archived", "passed": ok, "detail": detail})
    if not ok:
        return finish()

    own_ok, own_detail = check_ownership(canonical_repo, repo_slug, token)
    checklist.append({"label": "ownership proof", "passed": own_ok, "detail": own_detail})

    areas_ok, areas, areas_detail = check_areas(fields.get("Category", ""))
    checklist.append({"label": "category", "passed": areas_ok, "detail": areas_detail})

    bare_name = canonical_repo.split("/", 1)[1]
    collide_ok, collide_detail = check_collision(bare_name)
    checklist.append({"label": "no name collision", "passed": collide_ok, "detail": collide_detail})

    if not (own_ok and areas_ok and collide_ok):
        return finish()

    owner, name = canonical_repo.split("/", 1)
    file_path = REGISTRY_DIR / f"{owner}_{name}.yaml"
    entry = {
        "repo": canonical_repo,
        "name": fields.get("Display name", "").strip() or name,
        "areas": areas,
        "submitted_by": submitter,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }
    if fields.get("Contact (optional)"):
        entry["contact"] = fields["Contact (optional)"].strip()
    if fields.get("Spack package name (optional, if packaged)"):
        entry["spack_name"] = fields["Spack package name (optional, if packaged)"].strip()

    with open(file_path, "w") as f:
        yaml.safe_dump(entry, f, sort_keys=False)

    policy = load_policy()
    soft_ok, soft_checks = check_soft_gates(repo_json, submitter, policy)
    for label, passed, soft_detail in soft_checks:
        checklist.append({"label": label, "passed": passed, "detail": soft_detail})

    trust_ok, trust_detail = check_trust(submitter, token)
    checklist.append({"label": "trusted submitter", "passed": trust_ok, "detail": trust_detail})

    contrib_status, contrib_detail = check_contributor(canonical_repo, submitter, token)
    checklist.append({
        "label": "filer is a contributor",
        "passed": contrib_status != "fail",
        "detail": contrib_detail,
    })

    result.update(
        valid=True,
        auto_merge=soft_ok and trust_ok and contrib_status != "fail",
        repo=canonical_repo,
        file_path=str(file_path.relative_to(ROOT)),
    )
    finish()


if __name__ == "__main__":
    main()
