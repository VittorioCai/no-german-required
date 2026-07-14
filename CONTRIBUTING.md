# Contributing

Thanks for helping improve English Job Agent for Germany. Small, verified changes are the most useful.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m unittest discover -s tests -v
python -m src.main --dry-run
```

The dry run fetches public job sources but does not call an LLM, send notifications,
or change `data/seen.json`.

## Adding a company

Add one entry to `data/companies.yaml` and verify its public ATS endpoint responds.
Keep the change focused and include the endpoint you tested in the pull-request body.
Do not add sources that require login, bypass access controls, or prohibit automated access.

## Adding a source adapter

Implement the `Source` interface in `src/sources/`, return normalized `Job` objects,
use stable IDs, set request timeouts, and let one failed company/source degrade gracefully.
Add unit tests that mock network responses; CI tests must not depend on live endpoints.

## Pull requests

- Run the full unit-test suite and `python -m compileall -q src tests`.
- Update both English and Chinese READMEs when behavior or setup changes.
- Never commit API keys, app passwords, email addresses, or application notes.
- Explain the user impact and how you verified the change.
