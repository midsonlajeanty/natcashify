import re
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).parents[2]
DOCS: Final = ROOT / "docs"


def _config() -> str:
    return (ROOT / "mkdocs.yml").read_text(encoding="utf-8")


def _llmstxt_sections() -> str:
    return _config().split("  - llmstxt:", 1)[1].split("\nmarkdown_extensions:", 1)[0]


def _published_pages() -> set[str]:
    return {
        page.relative_to(DOCS).as_posix()
        for page in DOCS.rglob("*.md")
        if "superpowers" not in page.relative_to(DOCS).parts
    }


def test_every_documentation_page_is_listed_in_llms_txt() -> None:
    listed: set[str] = set()
    for pattern in re.findall(r"^\s+- ([\w/*.-]+\.md)$", _llmstxt_sections(), flags=re.MULTILINE):
        listed.update(page.relative_to(DOCS).as_posix() for page in DOCS.glob(pattern))
    assert _published_pages() <= listed


def test_every_documentation_page_is_in_the_nav() -> None:
    nav = _config().split("\nnav:", 1)[1]
    in_nav = set(re.findall(r":\s+([\w/-]+\.md)$", nav, flags=re.MULTILINE))
    assert _published_pages() <= in_nav


def test_llms_txt_also_ships_a_full_version() -> None:
    assert "full_output: llms-full.txt" in _llmstxt_sections()
