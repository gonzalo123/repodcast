from src.ai.prompts import episode_prompt
from src.domain.repository import RepositorySummary


def test_episode_prompt_requests_a_human_narrative_without_inventing_details() -> None:
    repository = RepositorySummary(
        name="demo",
        path="/demo",
        source_files=[],
        test_files=[],
        package_files=[],
        detected_stack=["Python"],
        entry_points=[],
        interesting_files=[],
    )

    prompt = episode_prompt(repository, "My demo", 3, "How is it wired?")

    assert "curious developer" in prompt
    assert "weekend\nexperiment" in prompt
    assert "Do not invent personal anecdotes" in prompt
    assert "Build ethos through technical precision" in prompt
    assert "Build subtle, credible pathos" in prompt
    assert "Build logos as a clear causal chain" in prompt
    assert "Every rhetorical device must improve understanding or recall" in prompt
    assert "Resolve the opening tension" in prompt
    assert "narrative arc rather than a feature inventory" in prompt
    assert "normally 55-110 words per scene" in prompt
    assert "be the integer 3" in prompt
    assert "Primary focus: How is it wired?" in prompt
