# .typecheck

Symlinks exposing one merged `natcashify` package, used only by Pyright through
`extraPaths = [".typecheck"]` in the root `pyproject.toml`.

In the workspace, `natcashify/__init__.py` (facade) and its subpackages (`natcashify.core`,
`natcashify.django`, ...) live in separate editable roots. Python merges them at runtime through
`pkgutil.extend_path`, but Pyright stops at the first regular `natcashify` package it finds and
cannot resolve the others. Installed wheels share one `site-packages/natcashify/` directory, so end
users never need this.

When adding a package, add its symlink:

```bash
ln -s ../../packages/natcashify-<name>/src/natcashify/<name> .typecheck/natcashify/<name>
```
