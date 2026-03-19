# Interview-QA Repo Notes

## Source And Local Checkout

- Upstream repository: `https://github.com/MITNKU/Interview-QA`
- Current workspace checkout: `C:\Users\zwh01\Documents\Playground\codex-artifacts\Interview-QA`
- Expected repo markers:
  - `README.md`
  - `pyproject.toml`
  - `src/interview_project_qa/cli.py`

## Pipeline Map

- `run`
  - normalize audio
  - diarize two speakers
  - slice speaker segments
  - transcribe speaker-separated chunks
  - assign interviewer vs candidate roles
  - extract project-related interviewer questions
  - generate improved technical answers
  - export Markdown locally
  - optionally publish to Notion
- `transcribe`
  - normalize audio
  - diarize two speakers
  - slice speaker segments
  - transcribe speaker-separated chunks
  - assign interviewer vs candidate roles
- `extract`
  - start from an existing `dialogue.json`
  - extract question groups
  - generate improved answers
- `export`
  - start from an existing `project_qa.json`
  - build local Markdown bundle
- `publish-notion`
  - start from an existing `project_qa.json`
  - publish through Notion API or hosted MCP

## Credential Facts From Current Code

- `HF_TOKEN`
  - required by `src/interview_project_qa/audio.py`
  - used to load `pyannote/speaker-diarization`
- `OPENAI_API_KEY`
  - required by `src/interview_project_qa/llm.py`
  - used for role assignment, question extraction, consolidation, and answer generation
- `transcribe` still requires OpenAI in the current upstream code
  - `src/interview_project_qa/pipeline.py` calls `assign_roles()` inside `run_transcription_only()`
- `NOTION_API_TOKEN`
  - required only for Notion REST publishing
- `NOTION_MCP_ACCESS_TOKEN`
  - required only for Notion MCP publishing
  - still depends on `OPENAI_API_KEY` in the current adapter path

## Output Structure

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

## Recommended Command Order

1. Run `python scripts/preflight.py --audio <path> --repo <repo-path>`.
2. Create and activate a virtual environment inside the repo checkout.
3. Run `pip install -e .`.
4. Run the smallest CLI command that matches the user request.
5. Report missing credentials before attempting a full pipeline run.
