import json
import tomllib
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).parents[2]
PACKAGES: Final = ROOT / "packages"
MARKER: Final = "# x-release-please-version"
INTERNAL_PIN_PREFIX: Final = "natcashify-core=="


def _load(package: Path) -> dict[str, Any]:
    return tomllib.loads((package / "pyproject.toml").read_text(encoding="utf-8"))


def _package_dirs() -> list[Path]:
    return sorted(path for path in PACKAGES.iterdir() if (path / "pyproject.toml").is_file())


def test_every_package_shares_the_facade_version() -> None:
    facade_version = _load(PACKAGES / "natcashify")["project"]["version"]
    for package in _package_dirs():
        project = _load(package)["project"]
        assert project["version"] == facade_version, package.name
        lines = (package / "pyproject.toml").read_text(encoding="utf-8").splitlines()
        version_lines = [line for line in lines if line.startswith("version = ")]
        assert [line.endswith(MARKER) for line in version_lines] == [True], package.name
        pins = [
            dependency
            for dependency in project.get("dependencies", [])
            if dependency.startswith("natcashify")
        ]
        for dependency in pins:
            assert dependency == f"{INTERNAL_PIN_PREFIX}{facade_version}", package.name
        pin_lines = [line for line in lines if INTERNAL_PIN_PREFIX in line]
        assert len(pin_lines) >= len(pins), package.name
        assert all(line.endswith(MARKER) for line in pin_lines), package.name


def test_the_facade_extras_pin_every_adapter_to_the_shared_version() -> None:
    facade = _load(PACKAGES / "natcashify")["project"]
    version = facade["version"]
    extras = facade["optional-dependencies"]
    assert extras == {
        name: [f"natcashify-{name}=={version}"] for name in ("django", "fastapi", "flask")
    }
    text = (PACKAGES / "natcashify" / "pyproject.toml").read_text(encoding="utf-8")
    extra_lines = [line for line in text.splitlines() if "natcashify-" in line and "==" in line]
    assert all(line.endswith(MARKER) for line in extra_lines)


def test_every_portion_has_a_typecheck_symlink() -> None:
    portions = sorted(PACKAGES.glob("natcashify-*/src/natcashify/*/"))
    assert portions
    for portion in portions:
        link = ROOT / ".typecheck" / "natcashify" / portion.name
        assert link.is_symlink(), portion.name
        assert link.resolve() == portion.resolve(), portion.name


def test_every_package_is_listed_in_release_config() -> None:
    config = json.loads((ROOT / "release" / "config.json").read_text(encoding="utf-8"))
    extra_files = set(config["packages"]["."]["extra-files"])
    expected = {f"packages/{package.name}/pyproject.toml" for package in _package_dirs()}
    assert extra_files == expected
