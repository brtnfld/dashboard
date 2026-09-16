#!/usr/bin/env python3
"""Validate a "Deregister a project" issue and, if a matching registry entry
exists, report enough for .github/workflows/deregister-project-request.yml
to open (and maybe auto-merge) a PR removing it.

Much simpler than process_registration.py: there's no ownership-proof file
to check (the entry already exists, proving someone once registered it) and
no areas/collision validation (nothing new is being asserted). The only
question is whether the filer is trusted enough to skip a maintainer.

Reads the raw issue body from stdin. Requires env vars ISSUE_AUTHOR and
GITHUB_TOKEN. Always exits 0 and prints one JSON object to stdout:
  {
    "valid": bool,       # a matching registry/<owner>_<repo>.yaml exists
    "auto_merge": bool,  # filer is a contributor to the repo, or trusted
    "repo": "Owner/repo" or null,
    "file_path": "registry/Owner_repo.yaml" or null,
    "checklist": [{"label": str, "passed": bool, "detail": str}, ...],
  }
"""

import json
import os
import re
import sys
from pathlib import Path

# Reuse process_registration's helpers rather than duplicating GitHub API
# and CODEOWNERS logic.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from process_registration import (  # noqa: E402
    ROOT,
    REGISTRY_DIR,
    check_contributor,
    check_trust,
    gh_get,
    parse_issue_form,
)


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

    owner, name = repo_slug.split("/", 1)
    file_path = REGISTRY_DIR / f"{owner}_{name}.yaml"
    if not file_path.exists():
        checklist.append({
            "label": "existing registration found",
            "passed": False,
            "detail": f"no {file_path.relative_to(ROOT)} -- nothing registered under that name",
        })
        return finish()
    checklist.append({"label": "existing registration found", "passed": True, "detail": str(file_path.name)})

    # Canonical case for the GitHub API calls below; the registry filename
    # itself is trusted as-is since it already matched an existing entry.
    resp = gh_get(f"/repos/{repo_slug}", token)
    canonical_repo = resp.json().get("full_name", repo_slug) if resp.status_code == 200 else repo_slug

    contrib_status, contrib_detail = check_contributor(canonical_repo, submitter, token)
    checklist.append({
        "label": "filer is a contributor",
        "passed": contrib_status != "fail",
        "detail": contrib_detail,
    })

    trust_ok, trust_detail = check_trust(submitter, token)
    checklist.append({"label": "trusted submitter", "passed": trust_ok, "detail": trust_detail})

    result.update(
        valid=True,
        auto_merge=trust_ok or contrib_status == "pass",
        repo=canonical_repo,
        file_path=str(file_path.relative_to(ROOT)),
    )
    finish()


if __name__ == "__main__":
    main()
