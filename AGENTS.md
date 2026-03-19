# AGENTS.md

## Repository expectations

- This repository implements a Codex-friendly skill for interview audio analysis.
- Keep deterministic work in Python code. Use the model for classification, extraction, synthesis, answer generation, and MCP-driven write actions.
- Prefer small pure functions and typed Pydantic schemas for all LLM I/O.
- Do not silently invent candidate experience. If a generated standard answer extends beyond the original response, mark it as an inferred or expanded answer in output notes.
- Keep Markdown output Notion-friendly: use headings, bullet lists sparingly, fenced code only when needed, and no HTML.
- Default workflow order:
  1. audio normalize/split
  2. speaker diarization
  3. transcription
  4. interviewer/candidate role assignment
  5. heuristic project-question candidate mining
  6. taxonomy-based question extraction and follow-up merge
  7. improved answer generation
  8. local Markdown export
  9. optional Notion API / MCP publish
- Prefer the Responses API for LLM steps and built-in web search when the workflow requests current factual verification.
- Prefer Notion's markdown APIs over low-level block APIs when writing whole pages.
- Before changing prompts, update prompt snapshots in `prompts/` and document the behavioral reason in `README.md`.

## Verification

- Run `python -m compileall src` after substantial code edits.
- Run `pytest` when changing parsing, export, classifier, or markdown formatting logic.

## Safety and privacy

- Interview audio and transcripts may contain personal data. Avoid uploading raw transcript segments to third-party services other than the explicitly configured model providers.
- Do not commit user audio, transcripts, generated outputs, or live Notion credentials.
