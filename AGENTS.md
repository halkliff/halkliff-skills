# Working in this repository

For an installation request, read README.md and run `python scripts/install.py`
from this checkout. It installs the complete dependency set. Do not install only
`skills/orchestrate-work`, overwrite a conflicting destination, or execute upstream
setup scripts. Use `--dest` for isolated checks.

For changes, apply pstack-principles and unslop. `dependencies.json` owns the file
mapping and upstream revisions. Keep upstream submodules unchanged except for an
explicit dependency update; Codex adaptations belong in `adapters/`.
Preserve `orchestrate-work`'s explicit-only invocation policy and upstream notices.

Verify installer changes with `python -m unittest discover -s tests -v`, followed
by a dry-run and real install into a temporary destination. Exercise the installed
artifacts; checking the source manifest alone is insufficient. Report runtime
orchestration as untested unless a live hierarchy was actually exercised.
