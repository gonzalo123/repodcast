from pathlib import Path

from src.repo.scanner import RepositoryScanner


def test_scanner_detects_stack_and_respects_gitignore(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    (tmp_path / "secret.py").write_text("password = 'nope'", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("secret.py\n", encoding="utf-8")
    summary = RepositoryScanner().scan(tmp_path)
    assert "Python" in summary.detected_stack
    assert "main.py" in summary.entry_points
    assert "secret.py" not in summary.source_tree
