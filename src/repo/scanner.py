from __future__ import annotations

import mimetypes
from pathlib import Path

import pathspec

from src.domain.repository import RepositoryFile, RepositorySummary

IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__"}
PACKAGE_NAMES = {
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "composer.json",
    "Gemfile",
}
LANGUAGES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".rs": "Rust",
    ".go": "Go",
    ".java": "Java",
    ".php": "PHP",
    ".rb": "Ruby",
    ".sh": "Shell",
    ".md": "Markdown",
    ".toml": "TOML",
    ".yaml": "YAML",
    ".yml": "YAML",
}
STACK_MARKERS = {
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "package.json": "Node.js",
    "Cargo.toml": "Rust",
    "go.mod": "Go",
    "pom.xml": "Java",
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "Makefile": "Make",
}


class RepositoryScanner:
    def __init__(self, max_file_bytes: int = 100_000, max_excerpt_chars: int = 4_000) -> None:
        self.max_file_bytes = max_file_bytes
        self.max_excerpt_chars = max_excerpt_chars

    def scan(self, path: Path) -> RepositorySummary:
        root = path.expanduser().resolve()
        if not root.is_dir():
            raise ValueError(f"Repository path is not a directory: {root}")
        spec = self._ignore_spec(root)
        files = sorted(
            (item for item in root.rglob("*") if self._include(root, item, spec)),
            key=lambda item: item.relative_to(root).as_posix(),
        )
        relative = [item.relative_to(root).as_posix() for item in files]
        readme_path = next((item for item in files if item.name.lower() == "readme.md"), None)
        package_files = [name for name in relative if Path(name).name in PACKAGE_NAMES]
        test_files = [name for name in relative if self._is_test(name)]
        source_files = [
            name for name in relative if self._is_source(name) and name not in test_files
        ]
        stack = sorted(
            {
                STACK_MARKERS[Path(name).name]
                for name in relative
                if Path(name).name in STACK_MARKERS
            }
        )
        stack.extend(
            sorted(
                {
                    LANGUAGES[Path(name).suffix]
                    for name in source_files
                    if Path(name).suffix in LANGUAGES and LANGUAGES[Path(name).suffix] not in stack
                }
            )
        )
        interesting = self._interesting(root, files, package_files, source_files, test_files)
        entries = [
            name
            for name in relative
            if Path(name).name
            in {"main.py", "app.py", "cli.py", "manage.py", "index.js", "index.ts"}
        ]
        return RepositorySummary(
            name=root.name,
            path=str(root),
            readme=self._read(readme_path) if readme_path else None,
            detected_stack=stack,
            package_files=package_files,
            source_files=source_files,
            test_files=test_files,
            entry_points=entries,
            source_tree=relative,
            interesting_files=interesting,
        )

    def _ignore_spec(self, root: Path) -> pathspec.GitIgnoreSpec:
        ignore = root / ".gitignore"
        lines = (
            ignore.read_text(encoding="utf-8", errors="replace").splitlines()
            if ignore.exists()
            else []
        )
        return pathspec.GitIgnoreSpec.from_lines(lines)

    def _include(self, root: Path, item: Path, spec: pathspec.GitIgnoreSpec) -> bool:
        rel = item.relative_to(root)
        if not item.is_file() or any(part in IGNORED_DIRS for part in rel.parts):
            return False
        if spec.match_file(rel.as_posix()) or item.stat().st_size > self.max_file_bytes:
            return False
        mime, _ = mimetypes.guess_type(item.name)
        return not (mime and not mime.startswith("text/") and item.suffix not in LANGUAGES)

    @staticmethod
    def _is_source(name: str) -> bool:
        return Path(name).suffix in LANGUAGES and not name.lower().endswith(
            (".md", ".yaml", ".yml", ".toml")
        )

    @staticmethod
    def _is_test(name: str) -> bool:
        path = Path(name)
        return (
            "tests" in path.parts
            or path.name.startswith("test_")
            or path.name.endswith(("_test.py", ".spec.ts", ".test.js"))
        )

    def _interesting(
        self,
        root: Path,
        files: list[Path],
        packages: list[str],
        sources: list[str],
        tests: list[str],
    ) -> list[RepositoryFile]:
        priorities = (
            packages
            + [
                name
                for name in sources
                if Path(name).name in {"main.py", "cli.py", "app.py", "index.ts", "index.js"}
            ]
            + sources[:6]
            + tests[:2]
        )
        unique = list(dict.fromkeys(priorities))[:12]
        result = []
        for name in unique:
            file = root / name
            reason = (
                "package manifest"
                if name in packages
                else "test"
                if name in tests
                else "source code"
            )
            result.append(
                RepositoryFile(
                    path=name,
                    language=LANGUAGES.get(file.suffix),
                    content_excerpt=self._read(file),
                    reason=reason,
                )
            )
        return result

    def _read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="replace")[: self.max_excerpt_chars]
