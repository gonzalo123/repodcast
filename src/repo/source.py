from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from git import Repo


@dataclass(frozen=True)
class ResolvedRepository:
    path: Path
    display_name: str
    source_url: str | None = None
    requested_ref: str | None = None
    commit_sha: str | None = None


class RepositorySourceResolver:
    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = (cache_dir or Path.home() / ".cache" / "repodcast" / "github").expanduser()

    def resolve(
        self, source: str, ref: str | None = None, refresh: bool = False
    ) -> ResolvedRepository:
        local = Path(source).expanduser()
        if local.is_dir():
            if ref:
                raise ValueError("--ref can only be used with a GitHub repository")
            return ResolvedRepository(path=local.resolve(), display_name=local.resolve().name)

        owner, repository, url = self._github_coordinates(source)
        checkout = self.cache_dir / owner / repository
        if refresh and checkout.exists():
            shutil.rmtree(checkout)
        if not checkout.exists():
            checkout.parent.mkdir(parents=True, exist_ok=True)
            clone_options = ["--depth=1", "--no-tags", "--no-recurse-submodules"]
            if ref:
                clone_options.extend(["--branch", ref])
            try:
                Repo.clone_from(
                    url,
                    checkout,
                    multi_options=clone_options,
                    env={**os.environ, "GIT_LFS_SKIP_SMUDGE": "1"},
                )
            except Exception:
                shutil.rmtree(checkout, ignore_errors=True)
                raise
        elif ref:
            repo = Repo(checkout)
            current_ref = repo.active_branch.name if not repo.head.is_detached else None
            if current_ref != ref:
                raise ValueError(
                    f"Cached checkout uses ref {current_ref or 'detached HEAD'}, not {ref}; use --refresh"
                )

        repo = Repo(checkout)
        return ResolvedRepository(
            path=checkout.resolve(),
            display_name=repository,
            source_url=url,
            requested_ref=ref,
            commit_sha=repo.head.commit.hexsha,
        )

    @staticmethod
    def _github_coordinates(source: str) -> tuple[str, str, str]:
        value = source.strip().rstrip("/")
        if value.startswith(("http://", "https://")):
            parsed = urlparse(value)
            if parsed.hostname not in {"github.com", "www.github.com"}:
                raise ValueError("Only github.com repository URLs are supported")
            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) != 2:
                raise ValueError("Use a GitHub repository URL; select branches with --ref")
            owner, repository = parts
        else:
            match = re.fullmatch(r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", value)
            if not match:
                raise ValueError("SOURCE must be a local directory, owner/repo, or a GitHub URL")
            owner, repository = match.groups()
        repository = repository.removesuffix(".git")
        if not owner or not repository:
            raise ValueError("Invalid GitHub repository")
        return owner, repository, f"https://github.com/{owner}/{repository}.git"
