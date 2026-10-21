import runpy
from pathlib import Path
from typing import Final

import pytest

EXAMPLES: Final = Path(__file__).parents[2] / "examples"


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("script.py", "order=ORDER-001 paid=True"),
        ("fastapi_app.py", "{'order': 'ORDER-001', 'status': 'paid'}"),
        ("flask_app.py", "{'order': 'ORDER-001', 'status': 'paid'}"),
    ],
)
def test_examples_run(name: str, expected: str, capsys: pytest.CaptureFixture[str]) -> None:
    runpy.run_path(str(EXAMPLES / name), run_name="__main__")
    assert expected in capsys.readouterr().out
