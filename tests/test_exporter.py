from pathlib import Path

from interview_project_qa.exporter import build_markdown_bundle, export_markdown
from interview_project_qa.models import ImprovedAnswer


def test_export_markdown(tmp_path: Path) -> None:
    items = [
        ImprovedAnswer(
            project_name="推荐系统",
            topic="架构设计",
            topic_category="architecture",
            priority="high",
            interviewer_question="你怎么设计重排链路？",
            merged_followups=["为什么这么分层？"],
            candidate_original_answer="我做了多目标排序。",
            gpt_deep_dive_answer="我会从召回、粗排、精排和重排几层来讲。",
            expansion_notes="补充了多阶段架构与指标。",
            answer_gaps=["缺少线上指标"],
            web_verified=False,
            citations=[],
        )
    ]
    out_dir = export_markdown(items, tmp_path, "Demo")
    assert (out_dir / "index.md").exists()
    content = (out_dir / "project-推荐系统.md").read_text(encoding="utf-8")
    assert "GPT 技术深挖版回答" in content
    assert "原回答缺口" in content


def test_build_markdown_bundle_contains_index() -> None:
    items = [
        ImprovedAnswer(
            project_name="AB实验平台",
            topic="业务结果",
            topic_category="business_impact",
            priority="medium",
            interviewer_question="这个平台最后带来了什么收益？",
            merged_followups=[],
            candidate_original_answer="缩短了实验发布周期。",
            gpt_deep_dive_answer="我们把实验配置与审计流程标准化后，发布效率和稳定性都提升了。",
            expansion_notes="补充了平台化收益表达。",
            answer_gaps=[],
            web_verified=False,
            citations=[],
        )
    ]
    bundle = build_markdown_bundle(items, "Demo")
    assert "index.md" in bundle
