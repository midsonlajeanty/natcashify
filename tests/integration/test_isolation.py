import ast
import subprocess
import sys
from pathlib import Path
from typing import Final

FORBIDDEN: Final = frozenset(
    {"django", "fastapi", "starlette", "flask", "werkzeug", "httpx", "httpx2"}
)
CORE_SOURCE: Final = Path(__file__).parents[2] / "packages" / "natcashify-core" / "src"


def test_importing_the_core_loads_no_framework() -> None:
    code = (
        "import sys, natcashify, natcashify.core;"
        "print(','.join(sorted({name.split('.')[0] for name in sys.modules})))"
    )
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert FORBIDDEN.isdisjoint(completed.stdout.strip().split(","))


def _imported_modules(path: Path) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
    return modules


def test_the_core_source_imports_only_the_standard_library() -> None:
    allowed = sys.stdlib_module_names | {"natcashify"}
    offenders = [
        f"{path.relative_to(CORE_SOURCE)}: {module}"
        for path in CORE_SOURCE.rglob("*.py")
        for module in _imported_modules(path)
        if module.split(".")[0] not in allowed
    ]
    assert offenders == []


ROOT: Final = Path(__file__).parents[2]
PUBLIC_SURFACES: Final = (
    "examples",
    "scripts",
    "docs",
    "packages/natcashify/src",
    "packages/natcashify-django",
    "packages/natcashify-fastapi",
    "packages/natcashify-flask",
)


def test_nothing_outside_the_core_imports_the_signing_internals() -> None:
    offenders = [
        str(path.relative_to(ROOT))
        for surface in PUBLIC_SURFACES
        for path in (ROOT / surface).rglob("*")
        if path.suffix in {".py", ".md"}
        and "superpowers" not in path.parts
        and "natcashify.core.signing" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
