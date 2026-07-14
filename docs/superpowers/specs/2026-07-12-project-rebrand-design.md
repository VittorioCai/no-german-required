# Project Rebrand Design

## Identity

- GitHub repository slug: `english-job-agent-germany`
- Display name: **English Job Agent for Germany**
- Tagline: **No German Required? Check before you apply.**
- Description: **Finds and ranks English-friendly student jobs in Germany, detects hidden German requirements, and sends a daily digest.**

The descriptive repository name is optimized for immediate comprehension and search. The old name remains only as the memorable tagline, with a question mark so it does not promise that every listed job requires no German.

## Repository Changes

Update the English and Chinese README headings and opening copy, the Python module docstring, email subject prefix, contribution guide, and license attribution. Add a regression test that rejects the old slug as a project name while allowing the tagline.

Do not rename Python modules, workflow names, secrets, state files, or application data because none of them encode the repository slug.

## GitHub Rename

After local tests pass and branding changes are pushed to the existing repository, rename the GitHub repository to `VittorioCai/english-job-agent-germany`. Then update the local `origin` URL and repository description.

No release, tag, branch, or replacement repository is created. GitHub's repository redirect preserves the old URL; the old slug must not be reused for another repository.

## Verification

- Full unit tests, compile check, and diff check pass before push.
- New repository URL resolves and reports `main` at the pushed commit.
- Old repository URL redirects to the new repository.
- Local `origin` uses the new URL.
- README and notification branding contain the display name; the old phrase appears only in the approved tagline.
