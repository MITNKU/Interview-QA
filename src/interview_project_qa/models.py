from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class AudioSegment(BaseModel):
    speaker: str
    start: float
    end: float
    text: str


class DialogueTurn(BaseModel):
    role: Literal["interviewer", "candidate", "unknown"]
    speaker: str
    start: float
    end: float
    text: str


class CandidateWindow(BaseModel):
    interviewer_turn_index: int
    interviewer_question: str
    question_start: float
    question_end: float
    candidate_answer: str
    answer_start: float | None = None
    answer_end: float | None = None
    heuristic_score: int = 0
    matched_signals: list[str] = Field(default_factory=list)
    project_hint_hits: list[str] = Field(default_factory=list)
    local_context: list[dict] = Field(default_factory=list)


class QuestionGroup(BaseModel):
    project_name: str = Field(description="Detected project name or inferred bucket")
    topic: str = Field(description="Question topic, e.g. architecture, optimization")
    topic_category: str = Field(description="Normalized topic taxonomy label")
    priority: Literal["high", "medium", "low"] = "medium"
    interviewer_question: str
    merged_followups: list[str] = Field(default_factory=list)
    candidate_original_answer: str
    answer_time_ranges: list[str] = Field(default_factory=list)
    relevance_reason: str
    project_confidence: float = 0.0
    question_confidence: float = 0.0
    heuristic_score: int = 0
    matched_signals: list[str] = Field(default_factory=list)


class ImprovedAnswer(BaseModel):
    project_name: str
    topic: str
    topic_category: str = "other_project"
    priority: Literal["high", "medium", "low"] = "medium"
    interviewer_question: str
    merged_followups: list[str] = Field(default_factory=list)
    candidate_original_answer: str
    gpt_deep_dive_answer: str
    expansion_notes: str
    answer_gaps: list[str] = Field(default_factory=list)
    web_verified: bool = False
    citations: list[str] = Field(default_factory=list)


class NotionPageRef(BaseModel):
    title: str
    mode: Literal["api", "mcp"]
    page_id: str | None = None
    url: str | None = None
    file_name: str | None = None


class PipelineResult(BaseModel):
    run_id: str
    source_audio: str
    title: str
    company: str | None = None
    project_hints: list[str] = Field(default_factory=list)
    transcript_path: str
    dialogue_path: str
    qa_json_path: str
    notion_export_dir: str
    notion_pages: list[NotionPageRef] = Field(default_factory=list)


class RunContext(BaseModel):
    run_id: str
    audio_path: Path
    title: str
    company: str | None = None
    project_hints: list[str] = Field(default_factory=list)
    web_search: bool = False
    notion_mode: Literal["local", "api", "mcp", "all"] = "local"
    notion_parent_page_id: str | None = None
    notion_index_page_id: str | None = None
