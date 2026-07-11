from src.domain.episode import Episode
from src.domain.repository import RepositorySummary
from src.domain.slide import ArchitectureFlow, FlowEdge, FlowNode, Slide


class FakeAiClient:
    def generate_episode(
        self,
        repository: RepositorySummary,
        title: str | None,
        minutes: int,
        focus: str | None = None,
    ) -> Episode:
        name = title or repository.name.replace("-", " ").title()
        stack = ", ".join(repository.detected_stack) or "a deliberately simple toolchain"
        source_count = len(repository.source_files)
        test_count = len(repository.test_files)
        opening = f"This episode explores {name}, from its source tree to the choices behind its implementation."
        if focus:
            opening = f"This episode explores {name} through one question: {focus}"
        topics = [
            (name, [focus or "A repository-to-video technical walkthrough"], opening),
            (
                "What is in the repository?",
                [f"{source_count} source files", f"Stack: {stack}"],
                f"The scanner finds {source_count} source files and identifies {stack}. It reads small, relevant excerpts while avoiding generated and binary content.",
            ),
            (
                "Architecture",
                ["Scan and summarize", "Plan content", "Render media"],
                "The pipeline separates repository analysis, content generation, narration, scenes, subtitles, and video rendering. Each external provider sits behind a small interface.",
            ),
            (
                "Command-line workflow",
                ["analyze", "episode", "audio, subtitles, render"],
                "The command line exposes every stage independently, which makes failed builds inspectable and lets users resume from generated artifacts.",
            ),
            (
                "Implementation detail",
                ["Typed Pydantic contracts", "Deterministic artifacts", "Provider isolation"],
                "Pydantic models form the contract between stages. Deterministic JSON and fake providers make the workflow repeatable without cloud credentials.",
            ),
            (
                "Testing and lessons",
                [
                    f"{test_count} repository test files detected",
                    "Fake adapters",
                    "Small integration surface",
                ],
                "Tests can exercise the entire orchestration using fake AI and audio clients. Production adapters remain thin and focused on AWS calls.",
            ),
            (
                "Takeaway",
                ["Inspectable", "Replaceable", "Ready to extend"],
                f"{name} demonstrates how a media pipeline can remain understandable: each intermediate artifact is useful, inspectable, and replaceable.",
            ),
        ]
        total_seconds = minutes * 60
        duration = max(1, total_seconds // len(topics))
        slides = [
            Slide(index=i, title=t, bullets=b, narration=n, duration_seconds=duration)
            for i, (t, b, n) in enumerate(topics, 1)
        ]
        slides[2] = slides[2].model_copy(
            update={
                "visual": ArchitectureFlow(
                    nodes=[
                        FlowNode(id="source", label="Repository", path="src/repo/scanner.py"),
                        FlowNode(id="episode", label="Episode", path="src/ai/prompts.py"),
                        FlowNode(id="audio", label="Voices", path="src/audio/renderer.py"),
                        FlowNode(id="video", label="Video", path="src/video/remotion.py"),
                    ],
                    edges=[
                        FlowEdge(**{"from": "source", "to": "episode"}),
                        FlowEdge(**{"from": "episode", "to": "audio"}),
                        FlowEdge(**{"from": "audio", "to": "video"}),
                    ],
                )
            }
        )
        slides[4] = slides[4].model_copy(
            update={
                "code_snippet": (
                    "repository = self.scanner.scan(repository_path)\n"
                    "episode = self.ai.generate_episode(repository, title, minutes)\n"
                    "audio = AudioRenderer(self.tts).render(episode, output_dir)"
                ),
                "code_language": "python",
                "code_path": "src/application/build_video.py",
            }
        )
        return Episode(title=name, target_minutes=minutes, slides=slides)
