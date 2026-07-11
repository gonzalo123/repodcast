import pytest
from pydantic import ValidationError

from src.domain.episode import Episode
from src.domain.slide import ArchitectureFlow, FlowEdge, FlowNode, Slide


def test_episode_requires_sequential_slide_indexes() -> None:
    slides = [Slide(index=2, title="Wrong", narration="Text", duration_seconds=1)]
    with pytest.raises(ValidationError, match="sequential"):
        Episode(title="Episode", target_minutes=1, slides=slides)


def test_architecture_flow_rejects_edges_to_unknown_nodes() -> None:
    with pytest.raises(ValidationError, match="existing nodes"):
        ArchitectureFlow(
            nodes=[FlowNode(id="cli", label="CLI"), FlowNode(id="video", label="Video")],
            edges=[FlowEdge(**{"from": "cli", "to": "missing"})],
        )
