from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .config import settings
from .models import ImprovedAnswer, NotionPageRef
from .utils import ensure_dir, slugify


def build_markdown_bundle(items: list[ImprovedAnswer], title: str) -> dict[str, str]:
    by_project: dict[str, list[ImprovedAnswer]] = defaultdict(list)
    for item in items:
        by_project[item.project_name].append(item)

    bundle: dict[str, str] = {}
    index_lines = [f"# {title}", "", "## 项目问答目录", ""]

    for project_name, group_items in by_project.items():
        slug = slugify(project_name)
        file_name = f"project-{slug}.md"
        index_lines.append(f"- [{project_name}]({file_name}) — {len(group_items)} 个问题")

        lines = [f"# {project_name}", ""]
        for idx, qa in enumerate(group_items, start=1):
            lines.extend([
                f"## Q{idx} · {qa.topic}",
                "",
                f"**分类**：{qa.topic_category}",
                "",
                f"**优先级**：{qa.priority}",
                "",
                "### 面试官问题",
                qa.interviewer_question,
                "",
            ])
            if qa.merged_followups:
                lines.append("### 合并追问")
                lines.extend([f"- {q}" for q in qa.merged_followups])
                lines.append("")
            lines.extend([
                "### 我的原始回答",
                qa.candidate_original_answer,
                "",
                "### GPT 技术深挖版回答",
                qa.gpt_deep_dive_answer,
                "",
                "### 扩写说明",
                qa.expansion_notes,
                "",
            ])
            if qa.answer_gaps:
                lines.append("### 原回答缺口")
                lines.extend([f"- {x}" for x in qa.answer_gaps])
                lines.append("")
            if qa.citations:
                lines.append("### 参考来源")
                lines.extend([f"- {c}" for c in qa.citations])
                lines.append("")
        bundle[file_name] = "\n".join(lines).strip() + "\n"

    bundle["index.md"] = "\n".join(index_lines).strip() + "\n"
    return bundle


def export_markdown(items: list[ImprovedAnswer], out_dir: Path, title: str) -> Path:
    notion_dir = ensure_dir(out_dir / "notion_exports")
    for file_name, content in build_markdown_bundle(items, title).items():
        (notion_dir / file_name).write_text(content, encoding="utf-8")
    return notion_dir


def publish_bundle_to_notion_api(bundle: dict[str, str], *, parent_page_id: str, index_page_id: str | None = None) -> list[NotionPageRef]:
    if not settings.notion_api_token:
        raise RuntimeError("NOTION_API_TOKEN is required for Notion API publishing.")
    from .notion_api import NotionAPIClient

    client = NotionAPIClient(token=settings.notion_api_token)
    pages: list[NotionPageRef] = []
    for file_name, content in bundle.items():
        title = file_name[:-3]
        if file_name == "index.md" and index_page_id:
            ref = client.replace_markdown_page(page_id=index_page_id, markdown=content, title=title)
        else:
            ref = client.create_markdown_page(parent_page_id=parent_page_id, markdown=content, title=title)
        ref.file_name = file_name
        pages.append(ref)
    return pages


def publish_bundle_to_notion_mcp(bundle: dict[str, str], *, parent_page_id: str) -> list[NotionPageRef]:
    from .notion_mcp import NotionMCPClient

    client = NotionMCPClient(
        openai_api_key=settings.openai_api_key,
        notion_mcp_access_token=settings.notion_mcp_access_token,
        notion_parent_page_id=parent_page_id,
    )
    pages: list[NotionPageRef] = []
    for file_name, content in bundle.items():
        title = file_name[:-3]
        ref = client.create_markdown_page(title=title, markdown=content)
        ref.file_name = file_name
        pages.append(ref)
    return pages
