from __future__ import annotations

from pathlib import Path

import typer
from rich import print

from .config import settings
from .exporter import export_markdown, publish_bundle_to_notion_api, publish_bundle_to_notion_mcp
from .llm import extract_project_questions, generate_improved_answers
from .models import ImprovedAnswer, RunContext
from .pipeline import run_full, run_transcription_only
from .utils import read_json, run_id, write_json

app = typer.Typer(help="Interview project QA pipeline skill")


@app.command()
def run(
    audio: Path = typer.Option(..., exists=True, help="Path to .m4a/.mp3 audio file"),
    title: str = typer.Option(..., help="Interview title"),
    company: str | None = typer.Option(None, help="Target company"),
    project_hints: str = typer.Option("", help="Comma-separated project names or hints"),
    web_search: bool = typer.Option(False, help="Enable OpenAI web search during answer generation"),
    notion_mode: str = typer.Option(settings.notion_mode, help="local | api | mcp | all"),
    notion_parent_page_id: str = typer.Option(settings.notion_parent_page_id, help="Notion parent page ID for API/MCP publishing"),
    notion_index_page_id: str = typer.Option(settings.notion_index_page_id, help="Existing Notion index page ID to replace"),
) -> None:
    hints = [x.strip() for x in project_hints.split(",") if x.strip()]
    result = run_full(
        audio=audio,
        title=title,
        company=company,
        project_hints=hints,
        web_search=web_search,
        notion_mode=notion_mode,
        notion_parent_page_id=notion_parent_page_id or None,
        notion_index_page_id=notion_index_page_id or None,
    )
    print("[green]Pipeline finished[/green]")
    print(result.model_dump_json(indent=2))


@app.command()
def transcribe(
    audio: Path = typer.Option(..., exists=True),
    title: str = typer.Option(...),
    company: str | None = typer.Option(None),
    project_hints: str = typer.Option(""),
) -> None:
    hints = [x.strip() for x in project_hints.split(",") if x.strip()]
    context = RunContext(run_id=run_id(), audio_path=audio, title=title, company=company, project_hints=hints)
    transcript_path, dialogue_path = run_transcription_only(context)
    print(f"[green]Transcript:[/green] {transcript_path}")
    print(f"[green]Dialogue:[/green] {dialogue_path}")


@app.command()
def extract(
    dialogue_json: Path = typer.Option(..., exists=True),
    title: str = typer.Option(...),
    company: str | None = typer.Option(None),
    project_hints: str = typer.Option(""),
    web_search: bool = typer.Option(False),
) -> None:
    hints = [x.strip() for x in project_hints.split(",") if x.strip()]
    dialogue = read_json(dialogue_json)
    groups = extract_project_questions(dialogue, hints)
    improved = generate_improved_answers(groups, title, company, web_search)
    out = dialogue_json.parent / "project_qa.json"
    write_json(out, [item.model_dump() for item in improved])
    print(f"[green]Generated:[/green] {out}")


@app.command()
def export(
    qa_json: Path = typer.Option(..., exists=True),
    title: str = typer.Option(...),
) -> None:
    items = [ImprovedAnswer(**x) for x in read_json(qa_json)]
    notion_dir = export_markdown(items, qa_json.parent, title)
    print(f"[green]Markdown exported:[/green] {notion_dir}")


@app.command("publish-notion")
def publish_notion(
    qa_json: Path = typer.Option(..., exists=True),
    title: str = typer.Option(...),
    mode: str = typer.Option("api", help="api | mcp"),
    parent_page_id: str = typer.Option(settings.notion_parent_page_id, help="Notion parent page ID"),
    index_page_id: str = typer.Option(settings.notion_index_page_id, help="Optional index page ID to replace"),
) -> None:
    items = [ImprovedAnswer(**x) for x in read_json(qa_json)]
    from .exporter import build_markdown_bundle

    bundle = build_markdown_bundle(items, title)
    if mode == "api":
        refs = publish_bundle_to_notion_api(bundle, parent_page_id=parent_page_id, index_page_id=index_page_id or None)
    elif mode == "mcp":
        refs = publish_bundle_to_notion_mcp(bundle, parent_page_id=parent_page_id)
    else:
        raise typer.BadParameter("mode must be one of: api, mcp")
    print("[green]Published pages:[/green]")
    print([ref.model_dump() for ref in refs])


if __name__ == "__main__":
    app()
