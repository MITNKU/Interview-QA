from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from openai import OpenAI

from .classifier import shortlist_project_question_windows
from .config import settings
from .models import CandidateWindow, DialogueTurn, ImprovedAnswer, QuestionGroup
from .utils import chunked


def _client() -> OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for LLM steps.")
    return OpenAI(api_key=settings.openai_api_key)


def _load_prompt(name: str) -> str:
    base = Path(__file__).resolve().parents[2] / "prompts"
    return (base / name).read_text(encoding="utf-8")


def assign_roles(dialogue_segments: Sequence[dict]) -> list[DialogueTurn]:
    client = _client()
    prompt = _load_prompt("role_assignment.md")
    resp = client.responses.create(
        model="gpt-5.4",
        input=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(dialogue_segments, ensure_ascii=False)},
        ],
        text={"format": {"type": "json_schema", "name": "role_assignment", "schema": {
            "type": "object",
            "properties": {
                "turns": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string", "enum": ["interviewer", "candidate", "unknown"]},
                            "speaker": {"type": "string"},
                            "start": {"type": "number"},
                            "end": {"type": "number"},
                            "text": {"type": "string"}
                        },
                        "required": ["role", "speaker", "start", "end", "text"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["turns"],
            "additionalProperties": False,
        }}},
    )
    payload = json.loads(resp.output_text)
    return [DialogueTurn(**item) for item in payload["turns"]]


def extract_project_questions(dialogue: Sequence[dict], project_hints: list[str]) -> list[QuestionGroup]:
    client = _client()
    prompt = _load_prompt("extract_project_questions.md")
    consolidate_prompt = _load_prompt("consolidate_project_questions.md")

    candidate_windows = shortlist_project_question_windows(list(dialogue), project_hints)
    if not candidate_windows:
        return []

    all_items: list[QuestionGroup] = []
    for batch in chunked(candidate_windows, settings.max_llm_candidate_windows_per_batch):
        user_payload = {
            "project_hints": project_hints,
            "candidate_windows": [item.model_dump() for item in batch],
        }
        resp = client.responses.create(
            model="gpt-5.4",
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            text={"format": {"type": "json_schema", "name": "project_question_groups", "schema": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": _question_group_schema()
                    }
                },
                "required": ["items"],
                "additionalProperties": False,
            }}},
        )
        payload = json.loads(resp.output_text)
        all_items.extend(QuestionGroup(**item) for item in payload["items"])

    resp = client.responses.create(
        model="gpt-5.4",
        input=[
            {"role": "system", "content": consolidate_prompt},
            {"role": "user", "content": json.dumps({"items": [x.model_dump() for x in all_items]}, ensure_ascii=False)},
        ],
        text={"format": {"type": "json_schema", "name": "project_question_groups_consolidated", "schema": {
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": _question_group_schema()}
            },
            "required": ["items"],
            "additionalProperties": False,
        }}},
    )
    payload = json.loads(resp.output_text)
    return [QuestionGroup(**item) for item in payload["items"]]


def _question_group_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "project_name": {"type": "string"},
            "topic": {"type": "string"},
            "topic_category": {"type": "string"},
            "priority": {"type": "string", "enum": ["high", "medium", "low"]},
            "interviewer_question": {"type": "string"},
            "merged_followups": {"type": "array", "items": {"type": "string"}},
            "candidate_original_answer": {"type": "string"},
            "answer_time_ranges": {"type": "array", "items": {"type": "string"}},
            "relevance_reason": {"type": "string"},
            "project_confidence": {"type": "number"},
            "question_confidence": {"type": "number"},
            "heuristic_score": {"type": "integer"},
            "matched_signals": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "project_name",
            "topic",
            "topic_category",
            "priority",
            "interviewer_question",
            "merged_followups",
            "candidate_original_answer",
            "answer_time_ranges",
            "relevance_reason",
            "project_confidence",
            "question_confidence",
            "heuristic_score",
            "matched_signals",
        ],
        "additionalProperties": False,
    }


def generate_improved_answers(items: Sequence[QuestionGroup], title: str, company: str | None, web_search: bool) -> list[ImprovedAnswer]:
    client = _client()
    prompt = _load_prompt("generate_improved_answer.md")
    tools = [{"type": "web_search"}] if web_search else []
    outputs: list[ImprovedAnswer] = []

    for item in items:
        user_payload = {
            "title": title,
            "company": company,
            "question_item": item.model_dump(),
        }
        resp = client.responses.create(
            model="gpt-5.4",
            tools=tools,
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            text={"format": {"type": "json_schema", "name": "improved_answer", "schema": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string"},
                    "topic": {"type": "string"},
                    "topic_category": {"type": "string"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                    "interviewer_question": {"type": "string"},
                    "merged_followups": {"type": "array", "items": {"type": "string"}},
                    "candidate_original_answer": {"type": "string"},
                    "gpt_deep_dive_answer": {"type": "string"},
                    "expansion_notes": {"type": "string"},
                    "answer_gaps": {"type": "array", "items": {"type": "string"}},
                    "web_verified": {"type": "boolean"},
                    "citations": {"type": "array", "items": {"type": "string"}}
                },
                "required": [
                    "project_name",
                    "topic",
                    "topic_category",
                    "priority",
                    "interviewer_question",
                    "merged_followups",
                    "candidate_original_answer",
                    "gpt_deep_dive_answer",
                    "expansion_notes",
                    "answer_gaps",
                    "web_verified",
                    "citations",
                ],
                "additionalProperties": False,
            }}},
        )
        outputs.append(ImprovedAnswer(**json.loads(resp.output_text)))
    return outputs
