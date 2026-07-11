from pydantic import BaseModel, ConfigDict, Field, model_validator


class DialogueTurn(BaseModel):
    model_config = ConfigDict(frozen=True)

    speaker: str = Field(min_length=1)
    text: str = Field(min_length=1)


class FlowNode(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1, max_length=32, pattern=r"^[a-zA-Z0-9_-]+$")
    label: str = Field(min_length=1, max_length=32)
    path: str | None = Field(default=None, max_length=80)


class FlowEdge(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    from_id: str = Field(alias="from", min_length=1)
    to_id: str = Field(alias="to", min_length=1)


class ArchitectureFlow(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: str = Field(default="flow", pattern="^flow$")
    nodes: list[FlowNode] = Field(min_length=2, max_length=6)
    edges: list[FlowEdge] = Field(min_length=1, max_length=7)

    @model_validator(mode="after")
    def edges_reference_nodes(self) -> "ArchitectureFlow":
        node_ids = {node.id for node in self.nodes}
        if len(node_ids) != len(self.nodes):
            raise ValueError("flow node ids must be unique")
        if any(edge.from_id not in node_ids or edge.to_id not in node_ids for edge in self.edges):
            raise ValueError("flow edges must reference existing nodes")
        return self


class Slide(BaseModel):
    model_config = ConfigDict(frozen=True)

    index: int = Field(ge=1)
    title: str = Field(min_length=1)
    bullets: list[str] = []
    narration: str | None = Field(default=None, min_length=1)
    dialogue: list[DialogueTurn] = []
    duration_seconds: int = Field(gt=0)
    visual_hint: str | None = None
    code_snippet: str | None = None
    code_language: str | None = Field(default=None, max_length=24)
    code_path: str | None = Field(default=None, max_length=120)
    visual: ArchitectureFlow | None = None

    @model_validator(mode="after")
    def has_spoken_content(self) -> "Slide":
        if not self.narration and not self.dialogue:
            raise ValueError("a slide must have narration or dialogue")
        return self

    @property
    def spoken_text(self) -> str:
        if self.dialogue:
            return "\n".join(f"{turn.speaker}: {turn.text}" for turn in self.dialogue)
        return self.narration or ""
