---
name: interview-project-qa
description: "Analyze interview recordings (.m4a or .mp3) with the MITNKU Interview-QA workflow: preflight the environment, run two-speaker diarization and transcription, assign interviewer vs candidate, extract project-focused interviewer questions, generate deeper technical answers, and export Markdown or publish to Notion. Use when Codex needs to work with interview audio, dialogue.json, project_qa.json, Notion publishing, or troubleshoot whether OPENAI_API_KEY, HF_TOKEN, ffmpeg, or repo setup are required."
---

# Interview Project QA

## Overview

Operate the Interview-QA repository in a predictable way. Start with preflight, then choose the smallest repo command that satisfies the request.

## Quick Start

1. Resolve the repo checkout first. Prefer an existing local checkout. In this workspace the expected path is `C:\Users\zwh01\Documents\Playground\codex-artifacts\Interview-QA`. If no checkout exists, clone `https://github.com/MITNKU/Interview-QA.git`.
2. Run `scripts/preflight.py --audio <path> --repo <repo-path>` before claiming the pipeline is runnable.
3. Read `references/repo-notes.md` when you need the command map, output structure, or credential matrix.
4. Surface blockers explicitly. Do not imply that the upstream `transcribe` command is local-only unless you have changed the repo code and verified that change.

## Workflow

### 1. Preflight

- Validate `ffmpeg` and `ffprobe`.
- Validate the audio path, file size, and duration.
- Validate that the repo checkout looks like the expected Interview-QA project.
- Report whether the current repo code path requires `HF_TOKEN`, `OPENAI_API_KEY`, and any Notion credentials.
- Use `scripts/preflight.py` for this step.

### 2. Choose The Execution Mode

- Use `preflight only` when credentials are missing or the user only wants input validation.
- Use `run` for the full pipeline from audio to `project_qa.json` and Markdown export.
- Use `transcribe` only when the user explicitly wants transcript and role-assigned dialogue output and the required credentials are present.
- Use `extract` when `dialogue.json` already exists and only question extraction plus answer generation is needed.
- Use `export` or `publish-notion` when `project_qa.json` already exists.

### 3. Run The Repo

- Use Python 3.11 or newer in an isolated virtual environment inside the repo checkout.
- Install dependencies in the repo before first run.
- Prefer `--notion-mode local` unless the user explicitly asks for Notion publishing and has the required credentials.
- Enable `--web-search` only when the user wants current factual verification in generated answers.

Use commands like these inside the repo checkout:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
interview-project-qa run --audio "C:\path\to\interview.m4a" --title "Company Interview" --project-hints "recommendation-system,ab-platform" --notion-mode local
```

```powershell
interview-project-qa extract --dialogue-json ".\output\runs\<run_id>\dialogue.json" --title "Company Interview" --project-hints "recommendation-system"
```

## Credential Matrix

- Require `HF_TOKEN` for diarization because the upstream repo loads `pyannote/speaker-diarization`.
- Require `OPENAI_API_KEY` for the current repo LLM steps.
- Treat the upstream `transcribe` command as requiring `OPENAI_API_KEY` too, because the current code still calls interviewer/candidate role assignment through OpenAI after Whisper transcription.
- Require `NOTION_API_TOKEN` only for `--notion-mode api`.
- Require `NOTION_MCP_ACCESS_TOKEN` only for `--notion-mode mcp`, alongside `OPENAI_API_KEY`.

## Failure Modes

- Stop early when `HF_TOKEN` is missing and the user asks for diarization or any upstream command that depends on it.
- Stop early when `OPENAI_API_KEY` is missing and the user asks for role assignment, question extraction, or answer generation.
- Stop early when `ffmpeg` or `ffprobe` is missing, because normalization and segment slicing will fail.
- Prefer a preflight result over guesswork when the repo state or dependency state is unclear.

## Resources

- Use `scripts/preflight.py` to validate the audio, repo path, binaries, and credential readiness.
- Read `references/repo-notes.md` for the current repo behavior and command boundaries.
