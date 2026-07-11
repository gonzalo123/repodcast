from pathlib import Path

import pytest
from git import Repo

from src.repo.source import RepositorySourceResolver


def test_resolves_a_local_directory(tmp_path: Path) -> None:
    resolved = RepositorySourceResolver(tmp_path / "cache").resolve(str(tmp_path))

    assert resolved.path == tmp_path.resolve()
    assert resolved.source_url is None


def test_clones_and_reuses_a_cached_repository(tmp_path: Path) -> None:
    remote = tmp_path / "remote"
    remote.mkdir()
    repo = Repo.init(remote)
    (remote / "README.md").write_text("# Demo", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("initial")
    resolver = RepositorySourceResolver(tmp_path / "cache")
    resolver._github_coordinates = lambda source: ("owner", "demo", remote.as_uri())  # type: ignore[method-assign]

    first = resolver.resolve("owner/demo")
    second = resolver.resolve("owner/demo")

    assert first.path == second.path
    assert first.commit_sha == repo.head.commit.hexsha
    assert (first.path / "README.md").exists()


def test_rejects_non_github_urls(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="github.com"):
        RepositorySourceResolver(tmp_path).resolve("https://example.com/owner/repo")
