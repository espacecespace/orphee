from __future__ import annotations

from streamlit.testing.v1 import AppTest


def test_streamlit_app_starts_without_exception() -> None:
    app = AppTest.from_file("app.py").run(timeout=30)

    assert not app.exception
    assert len(app.button) >= 1
