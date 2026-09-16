# Project registry

This is the self-service front door for tracking a repo that isn't in the
[CASS software catalog](https://github.com/cass-community/cass-community.github.io) --
if your project is already CASS-stewarded, add it there instead (a
`_software/<name>.md` file); it flows into this dashboard automatically.

One YAML file per project, named `<owner>_<repo>.yaml` after the GitHub
`owner/repo`. Copy [TEMPLATE.yaml](TEMPLATE.yaml) to get started; it documents
every field.

## How to register

File the **"Register a project"** issue form in this repo's Issues tab -- a
workflow validates it and opens the PR for you. This is the only supported
way in: a hand-authored PR adding a `registry/*.yaml` file directly skips
every automated check (ownership proof, category, name collision, filer
verification) and won't be accepted.

Before you register:

1. Add `.corsa/metrics.yaml` to the root of **your own repo** (not this one),
   with a `repo:` field matching what you're registering here. This is how
   the workflow verifies you actually control the repo. See the
   [metrics collector's docs/PROJECT_CONFIG.md](https://github.com/corsa-center/metrics/blob/main/docs/PROJECT_CONFIG.md)
   for the file's format -- it also lets you control which metrics get
   collected about your project.
2. Make sure the repo is public and not archived.

## What happens next

A workflow checks: the YAML is well-formed, the repo exists and is public,
`.corsa/metrics.yaml` is present with a matching `repo:` field, the `areas`
values are valid, and the entry doesn't collide with an existing one. If all
of that passes, a PR is opened either way -- your registration is never
silently dropped.

Whether that PR merges automatically depends on two more things: whether
*you* (the GitHub account filing the issue, not just whoever once added
`.corsa/metrics.yaml`) show up in the target repo's own commit history, and
whether you're a recognized submitter (listed in [CODEOWNERS](CODEOWNERS)).
Both exist because the file alone only proves *someone* had authority over
the repo at some point -- not that the person filing this particular
registration does. If either is missing, the PR is left open for a
maintainer instead, and the issue comment says exactly what's still needed.

Once merged, your project appears in the catalog on the next nightly data
update (typically within a day).

## Removing a project

File the **"Deregister a project"** issue form, naming the repo exactly as it
was registered. It merges automatically if you show up in that repo's own
commit history or are a recognized submitter -- same bar as registering it in
the first place. Otherwise it still opens a PR, just left for a maintainer.

A maintainer can also remove any entry directly via the "Deregister project"
`workflow_dispatch` action, without going through an issue.
