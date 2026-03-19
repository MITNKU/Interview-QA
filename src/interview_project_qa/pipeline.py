from __future__ import annotations

from pathlib import Path

from .audio import diarize_two_speakers, normalize_audio, slice_segments
from .config import settings
from .exporter import build_markdown_bundle, export_markdown, publish_bundle_to_notion_api, publish_bundle_to_notion_mcp
from .llm import assign_roles, extract_project_questions, generate_improved_answers
from .models import PipelineResult, RunContext
from .transcribe import transcribe_segments
from .utils import ensure_dir, read_json, run_id, write_json


def pipeline_dirs(context: RunContext) -> tuple[Path, Path]:
    run_root = ensure_dir(settings.output_dir / "runs" / context.run_id)
    work_dir = ensure_dir(run_root / "work")
    return run_root, work_dir


def run_transcription_only(context: RunContext) -> tuple[Path, Path]:
    run_root, work_dir = pipeline_dirs(context)
    normalized = normalize_audio(context.audio_path, work_dir)
    diarized = diarize_two_speakers(normalized)
    chunk_items = slice_segments(normalized, diarized, work_dir)
    transcript = transcribe_segments([(speaker, str(path), start, end) for speaker, path, start, end in chunk_items])
    transcript_path = run_root / "transcript.json"
    write_json(transcript_path, [item.model_dump() for item in transcript])

    role_input = [item.model_dump() for item in transcript]
    dialogue = assign_roles(role_input)
    dialogue_path = run_root / "dialogue.json"
    write_json(dialogue_path, [item.model_dump() for item in dialogue])
    return transcript_path, dialogue_path


def run_full(
    audio: Path,
    title: str,
    company: str | None,
    project_hints: list[str],
    web_search: bool,
    notion_mode: str = "local",
    notion_parent_page_id: str | None = None,
    notion_index_page_id: str | None = None,
) -> PipelineResult:
    context = RunContext(
        run_id=run_id(),
        audio_path=audio,
        title=title,
        company=company,
        project_hints=project_hints,
        web_search=web_search,
        notion_mode=notion_mode,  # type: ignore[arg-type]
        notion_parent_page_id=notion_parent_page_id,
        notion_index_page_id=notion_index_page_id,
    )
    run_root, _ = pipeline_dirs(context)
    transcript_path, dialogue_path = run_transcription_only(context)
    dialogue = read_json(dialogue_path)
    question_groups = extract_project_questions(dialogue, project_hints)
    improved = generate_improved_answers(question_groups, title, company, web_search)
    qa_json_path = run_root / "project_qa.json"
    write_json(qa_json_path, [item.model_dump() for item in improved])
    notion_dir = export_markdown(improved, run_root, title)

    notion_pages = []
    effective_parent = notion_parent_page_id or settings.notion_parent_page_id or None
    effective_index = notion_index_page_id or settings.notion_index_page_id or None
    bundle = build_markdown_bundle(improved, title)
    if notion_mode in {"api", "all"} and effective_parent:
        notion_pages.extend(publish_bundle_to_notion_api(bundle, parent_page_id=effective_parent, index_page_id=effective_index or None))
    if notion_mode in {"mcp", "all"} and effective_parent:
        notion_pages.extend(publish_bundle_to_notion_mcp(bundle, parent_page_id=effective_parent))

    return PipelineResult(
        run_id=context.run_id,
        source_audio=str(audio),
        title=title,
        company=company,
        project_hints=project_hints,
        transcript_path=str(transcript_path),
        dialogue_path=str(dialogue_path),
        qa_json_path=str(qa_json_path),
        notion_export_dir=str(notion_dir),
        notion_pages=notion_pages,
    )
