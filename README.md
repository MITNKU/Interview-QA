# interview-project-qa-skill

A Codex-friendly repository scaffold for a reusable skill that:

1. ingests a long interview recording (`.m4a` / `.mp3`),
2. performs **speaker diarization first**,
3. merges fragmented speaker turns into more stable transcription chunks,
4. transcribes speaker-separated segments,
5. identifies **interviewer** vs **candidate**,
6. extracts only **project-related interviewer questions**,
7. merges follow-up questions into one topic group,
8. generates a **technical deep-dive GPT answer** for each group, with optional web search,
9. exports **Notion-friendly Markdown** files locally,
10. optionally writes those pages directly into Notion through the **Notion API** or **Notion MCP**.

## What changed in the second-stage enhancement

This repository now includes three major upgrades:

- **Direct Notion publishing**
  - Local Markdown export is still preserved.
  - New Notion API publishing path uses Notion's markdown page APIs.
  - New Notion MCP publishing path uses OpenAI Responses remote MCP tooling against Notion's hosted MCP server.
- **Stronger project-question classification**
  - Added a heuristic prefilter for long transcripts.
  - Added taxonomy-based extraction and a second consolidation pass.
  - Keeps collaboration / conflict / business-impact questions, while still prioritizing pure technical depth.
- **More stable long-audio chunking**
  - Adjacent same-speaker diarization segments are merged.
  - Oversized turns are re-split into bounded transcription chunks.
  - Transcription output is merged back into longer coherent turns.

## Why this shape

- `AGENTS.md` gives Codex project-wide rules and workflow expectations.
- `.agents/skills/interview-project-qa/SKILL.md` gives a reusable skill manifest close to the codebase.
- deterministic preprocessing stays in Python.
- subjective extraction and answer synthesis use the model.
- Notion publishing is isolated behind adapters so you can keep local-only, API, or MCP workflows.

## Requirements

- Python 3.11+
- `ffmpeg` and `ffprobe` on PATH
- `OPENAI_API_KEY`
- `HF_TOKEN` for pyannote diarization models
- For Notion API publishing: `NOTION_API_TOKEN`
- For Notion MCP publishing: `NOTION_MCP_ACCESS_TOKEN`

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

## Basic usage

### Local Markdown only

```bash
interview-project-qa run \
  --audio /absolute/path/interview.m4a \
  --title "ByteDance Backend Interview - 2026-03-19" \
  --project-hints "推荐系统重排, AB实验平台, 数据中台" \
  --company "ByteDance" \
  --web-search \
  --notion-mode local
```

### Direct write through Notion API

```bash
interview-project-qa run \
  --audio /absolute/path/interview.m4a \
  --title "ByteDance Backend Interview - 2026-03-19" \
  --project-hints "推荐系统重排, AB实验平台" \
  --web-search \
  --notion-mode api \
  --notion-parent-page-id "YOUR_NOTION_PARENT_PAGE_ID"
```

### Direct write through Notion MCP

```bash
interview-project-qa run \
  --audio /absolute/path/interview.m4a \
  --title "ByteDance Backend Interview - 2026-03-19" \
  --project-hints "推荐系统重排, AB实验平台" \
  --web-search \
  --notion-mode mcp \
  --notion-parent-page-id "YOUR_NOTION_PARENT_PAGE_ID"
```

## Output structure

```text
output/
  runs/<run_id>/
    transcript.json
    dialogue.json
    project_qa.json
    notion_exports/
      index.md
      project-<slug>.md
```

When `--notion-mode api|mcp|all` is enabled and credentials are present, the CLI also returns created page IDs and URLs.

## Notion API path

This repository uses Notion's markdown-oriented content APIs:

- `POST /v1/pages` with `markdown` creates pages from markdown
- `GET /v1/pages/:page_id/markdown` reads pages as markdown
- `PATCH /v1/pages/:page_id/markdown` supports `replace_content` and `update_content`

Those APIs are now part of Notion's official markdown content workflow and are especially well-suited for agentic tools and markdown-native export pipelines. citeturn911171view2turn961070search0turn913502search5

## Notion MCP path

Notion now provides an official hosted MCP server. The docs describe:

- hosted endpoints at `https://mcp.notion.com/mcp` and `/sse`
- OAuth-based access tokens for MCP clients
- write-capable tools including `notion-create-pages` and `notion-update-page`

This repository's MCP adapter assumes you already have a valid MCP access token and uses the OpenAI Responses API remote MCP tool surface to call Notion. citeturn969319search0turn699377view0turn873981view0turn755109search2

## Notion permissions you need

For the REST API path, the integration must have access to the parent page and the relevant insert capabilities. Notion's docs call out that page creation requires the integration to be connected to the target page, and markdown page creation requires insert content / insert property capabilities. citeturn602906search13turn911171view2turn399930view0

## CLI commands

### `run`
Full pipeline, with optional Notion publishing.

### `transcribe`
Only run normalization, diarization, transcription, and role assignment.

### `extract`
Run question extraction from an existing dialogue JSON.

### `export`
Rebuild local Markdown from an existing `project_qa.json`.

### `publish-notion`
Publish an existing `project_qa.json` bundle into Notion through API or MCP.

## Known constraints

- diarization accuracy still depends on recording quality and overlap.
- the Notion MCP path assumes you already handled OAuth and have an access token available.
- the Notion MCP adapter is a practical scaffold, but may still need prompt tuning against your specific workspace structure.
- very large transcripts can still be noisy if the source audio contains heavy crosstalk.

## Suggested next upgrades

- add confidence evaluation fixtures for the classifier
- add per-project answer style templates
- add automatic Notion page update instead of always creating child pages
- add transcript QA grading and red-flag detection for weak answers
