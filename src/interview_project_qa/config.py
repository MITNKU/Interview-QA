from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    hf_token: str = os.getenv("HF_TOKEN", "")
    output_dir: Path = Path(os.getenv("INTERVIEW_QA_OUTPUT_DIR", "./output"))
    whisper_model_size: str = os.getenv("WHISPER_MODEL_SIZE", "medium")
    whisper_device: str = os.getenv("WHISPER_DEVICE", "cpu")
    whisper_compute_type: str = os.getenv("WHISPER_COMPUTE_TYPE", "default")

    diarization_gap_seconds: float = float(os.getenv("DIARIZATION_GAP_SECONDS", "0.8"))
    diarization_padding_seconds: float = float(os.getenv("DIARIZATION_PADDING_SECONDS", "0.25"))
    max_transcribe_chunk_seconds: float = float(os.getenv("MAX_TRANSCRIBE_CHUNK_SECONDS", "75"))
    max_merged_speaker_seconds: float = float(os.getenv("MAX_MERGED_SPEAKER_SECONDS", "180"))
    max_llm_candidate_windows_per_batch: int = int(os.getenv("MAX_LLM_CANDIDATE_WINDOWS_PER_BATCH", "18"))

    notion_mode: str = os.getenv("NOTION_MODE", "local")
    notion_api_token: str = os.getenv("NOTION_API_TOKEN", "")
    notion_parent_page_id: str = os.getenv("NOTION_PARENT_PAGE_ID", "")
    notion_index_page_id: str = os.getenv("NOTION_INDEX_PAGE_ID", "")
    notion_title_property: str = os.getenv("NOTION_TITLE_PROPERTY", "title")
    notion_version: str = os.getenv("NOTION_VERSION", "2026-03-11")

    notion_mcp_access_token: str = os.getenv("NOTION_MCP_ACCESS_TOKEN", "")
    notion_mcp_server_url: str = os.getenv("NOTION_MCP_SERVER_URL", "https://mcp.notion.com/mcp")


settings = Settings()
