from __future__ import annotations

from pathlib import Path

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from src.application.build_video import BuildEvent


class BuildDashboard:
    STAGES = ("resolve", "scan", "episode", "audio", "subtitles", "render")
    LABELS = {
        "resolve": "Resolve repository",
        "scan": "Analyze source",
        "episode": "Write the episode",
        "audio": "Generate voices",
        "subtitles": "Create subtitles",
        "render": "Render video",
    }

    def __init__(
        self,
        console: Console,
        repository: str,
        minutes: int,
        focus: str | None,
        quiet: bool = False,
    ) -> None:
        self.console = console
        self.quiet = quiet
        self.interactive = console.is_terminal and not quiet
        subtitle = (
            f"[cyan]{repository}[/cyan] · {minutes} minute{'s' if minutes != 1 else ''}"
        )
        if focus:
            subtitle += f"\n[dim]“{focus}”[/dim]"
        self.header = Panel(
            subtitle,
            title="[bold magenta]REPODCAST[/bold magenta]",
            border_style="magenta",
        )
        self.progress = Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("{task.description}", justify="left"),
            BarColumn(bar_width=24),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        )
        self.tasks: dict[str, TaskID] = {
            stage: self.progress.add_task(
                self.LABELS[stage], total=1, visible=stage == "resolve"
            )
            for stage in self.STAGES
        }
        self.live: Live | None = None

    def __enter__(self) -> BuildDashboard:
        if self.interactive:
            self.live = Live(
                Group(self.header, self.progress),
                console=self.console,
                refresh_per_second=10,
            )
            self.live.start()
        return self

    def __exit__(self, *args: object) -> None:
        if self.live:
            self.live.stop()

    def start(self, stage: str, total: int = 1) -> None:
        if self.quiet:
            return
        task = self.tasks[stage]
        self.progress.update(task, visible=True, total=total, completed=0)

    def complete(self, stage: str, detail: str | None = None) -> None:
        if self.quiet:
            return
        task = self.tasks[stage]
        description = self.LABELS[stage]
        if detail:
            description += f" [dim]· {detail}[/dim]"
        self.progress.update(
            task, description=description, completed=self.progress.tasks[task].total
        )
        if not self.interactive:
            self.console.print(f"[green]✓[/green] {description}")

    def event(self, event: BuildEvent) -> None:
        if self.quiet:
            return
        task = self.tasks[event.stage]
        self.progress.update(
            task, visible=True, total=event.total, completed=event.completed
        )
        if event.completed >= event.total:
            self.complete(event.stage, event.detail)

    def success(self, output: Path, scenes: int, duration: int, subtitles: str) -> None:
        if self.quiet:
            self.console.print(output)
            return
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold")
        table.add_column(style="cyan")
        table.add_row("Video", str(output))
        table.add_row("Scenes", str(scenes))
        table.add_row("Duration", f"{duration // 60:02}:{duration % 60:02}")
        table.add_row("Subtitles", subtitles)
        self.console.print(
            Panel(
                table,
                title="[bold green]VIDEO READY[/bold green]",
                border_style="green",
            )
        )

    def failure(self, error: Exception) -> None:
        if not self.quiet:
            self.console.print(
                Panel(
                    str(error),
                    title="[bold red]BUILD FAILED[/bold red]",
                    border_style="red",
                )
            )
