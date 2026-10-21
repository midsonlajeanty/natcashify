# Natcashify

uv workspace of independently published packages sharing the `natcashify` import namespace. A typed
Python SDK for the NatCash payment gateway.

## Layout

- `packages/natcashify-core`: framework-agnostic engine, standard library only. It must never
  import `django`, `fastapi`, `starlette`, `flask`, `werkzeug`, `httpx` or `httpx2`;
  `tests/integration/test_isolation.py` enforces it.
- `packages/natcashify-{django,fastapi,flask}`: optional adapters.
- `packages/natcashify`: facade distribution. It alone owns `natcashify/__init__.py`; every other
  package is a namespace portion. `pkgutil.extend_path` in that file makes editable installs work.

## Rules

- `.typecheck/natcashify` is a symlink tree merging the facade and every portion, because Pyright
  cannot merge a regular package with namespace portions spread over several editable roots.
  Add a symlink there when adding a package.
- Internal dependency pins and versions carry `# x-release-please-version`; release-please
  (`release/`) bumps them all together.
- The sandbox is the default environment everywhere, including `from_env` and the adapters.
- Wire-contract tests compare against vectors generated from the PHP SDK
  (`scripts/php_vectors.php`, output in `packages/natcashify-core/tests/fixtures/php_vectors.json`).
  Regenerate the fixture with the PHP script; never edit it by hand.
- No test touches the network unless its opt-in environment variables are set.

## Tooling decisions

- Ruff ignores `TC001`-`TC003` because FastAPI and Django resolve annotations at runtime, so
  typing-only imports must stay real imports.
- uv resolves with `exclude-newer = "7 days"`.

## Commands

```bash
uv sync --all-packages
uv run pytest
uv run pyright
uv run ruff check . && uv run ruff format --check .
uv run --only-group docs mkdocs build --strict
```
