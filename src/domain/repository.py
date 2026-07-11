from pydantic import BaseModel, ConfigDict


class RepositoryFile(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: str
    language: str | None = None
    content_excerpt: str
    reason: str


class RepositorySummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    path: str
    readme: str | None = None
    detected_stack: list[str]
    package_files: list[str]
    source_files: list[str]
    test_files: list[str]
    entry_points: list[str] = []
    source_tree: list[str] = []
    interesting_files: list[RepositoryFile]
    source_url: str | None = None
    requested_ref: str | None = None
    commit_sha: str | None = None
