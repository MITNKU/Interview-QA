from __future__ import annotations

import re
from typing import Iterable

from .models import CandidateWindow, DialogueTurn

PROJECT_KEYWORDS = {
    "项目", "系统", "架构", "模块", "平台", "链路", "服务", "接口", "方案", "落地", "上线", "优化", "性能", "指标",
    "结果", "效果", "收益", "协作", "推动", "冲突", "排查", "稳定性", "扩展性", "吞吐", "延迟", "召回", "排序",
    "项目里", "项目中", "负责", "难点", "挑战", "tradeoff", "architecture", "design", "latency", "throughput", "pipeline",
    "service", "system", "project", "ownership", "impact", "collaboration", "conflict", "stakeholder",
}

TECH_PRIORITY_KEYWORDS = {
    "架构", "系统", "设计", "实现", "优化", "性能", "稳定性", "高可用", "扩展", "tradeoff", "consistency", "cache",
    "db", "database", "queue", "rpc", "api", "schema", "监控", "故障", "排查", "压测", "延迟", "吞吐",
}

COLLAB_BUSINESS_KEYWORDS = {
    "协作", "推动", "冲突", "对齐", "业务", "收益", "指标", "结果", "落地", "stakeholder", "impact", "result",
}

QUESTION_PATTERNS = [re.compile(p, re.I) for p in [r"\?", r"吗[？?]?$", r"怎么", r"为什么", r"如何", r"你.*负责", r"can you", r"how did", r"why did"]]


def _contains_question_signal(text: str) -> bool:
    return any(p.search(text) for p in QUESTION_PATTERNS)


def _keyword_hits(text: str, keywords: Iterable[str]) -> list[str]:
    lowered = text.lower()
    return [kw for kw in keywords if kw.lower() in lowered]


def shortlist_project_question_windows(dialogue: list[dict] | list[DialogueTurn], project_hints: list[str]) -> list[CandidateWindow]:
    turns = [turn if isinstance(turn, DialogueTurn) else DialogueTurn(**turn) for turn in dialogue]
    out: list[CandidateWindow] = []
    for idx, turn in enumerate(turns):
        if turn.role != "interviewer":
            continue
        if not _contains_question_signal(turn.text):
            continue

        project_hits = _keyword_hits(turn.text, project_hints)
        base_hits = _keyword_hits(turn.text, PROJECT_KEYWORDS)
        tech_hits = _keyword_hits(turn.text, TECH_PRIORITY_KEYWORDS)
        collab_hits = _keyword_hits(turn.text, COLLAB_BUSINESS_KEYWORDS)
        score = 0
        score += 2 if base_hits else 0
        score += 2 * len(project_hits)
        score += 2 if tech_hits else 0
        score += 1 if collab_hits else 0
        if "项目" in turn.text or "project" in turn.text.lower():
            score += 2
        if score <= 0:
            continue

        local_context: list[dict] = [turn.model_dump()]
        answer_turns: list[DialogueTurn] = []
        cursor = idx + 1
        while cursor < len(turns):
            nxt = turns[cursor]
            local_context.append(nxt.model_dump())
            if nxt.role == "interviewer":
                break
            if nxt.role == "candidate":
                answer_turns.append(nxt)
            cursor += 1

        answer_text = "\n".join(t.text for t in answer_turns).strip()
        out.append(
            CandidateWindow(
                interviewer_turn_index=idx,
                interviewer_question=turn.text,
                question_start=turn.start,
                question_end=turn.end,
                candidate_answer=answer_text,
                answer_start=answer_turns[0].start if answer_turns else None,
                answer_end=answer_turns[-1].end if answer_turns else None,
                heuristic_score=score,
                matched_signals=sorted(set(base_hits + tech_hits + collab_hits)),
                project_hint_hits=project_hits,
                local_context=local_context,
            )
        )
    return out
