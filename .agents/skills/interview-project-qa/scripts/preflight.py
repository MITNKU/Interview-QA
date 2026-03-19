from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


REQUIRED_REPO_MARKERS = (
    "README.md",
    "pyproject.toml",
    "src/interview_project_qa/cli.py",
)


def default_repo_candidates() -> list[Path]:
    cwd = Path.cwd()
    script_path = Path(__file__).resolve()
    return [
        cwd / "Interview-QA",
        cwd / "codex-artifacts" / "Interview-QA",
        script_path.parents[4],
        Path(os.getenv("INTERVIEW_QA_REPO", "")) if os.getenv("INTERVIEW_QA_REPO") else Path(),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preflight validation for the MITNKU Interview-QA repo."
    )
    parser.add_argument("--audio", required=True, help="Path to the input .m4a or .mp3 file.")
    parser.add_argument("--repo", help="Path to an existing Interview-QA checkout.")
    parser.add_argument(
        "--title",
        default="Interview Session",
        help="Optional title used only when printing example run commands.",
    )
    parser.add_argument(
        "--project-hints",
        default="",
        help="Comma-separated project hints used only when printing example run commands.",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Print JSON only, without the short human-readable summary.",
    )
    return parser.parse_args()


def is_repo_checkout(path: Path) -> bool:
    return path.is_dir() and all((path / marker).exists() for marker in REQUIRED_REPO_MARKERS)


def resolve_repo(explicit: str | None) -> Path | None:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    candidates.extend(default_repo_candidates())
    for candidate in candidates:
        if not str(candidate):
            continue
        resolved = candidate.expanduser()
        if is_repo_checkout(resolved):
            return resolved.resolve()
    return None


def probe_duration(audio_path: Path) -> float | None:
    if shutil.which("ffprobe") is None:
        return None
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(audio_path),
    ]
    try:
        proc = subprocess.run(command, check=True, capture_output=True, text=True)
    except (subprocess.CalledProcessError, OSError, ValueError):
        return None
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return None


def format_duration(seconds: float | None) -> str | None:
    if seconds is None:
        return None
    total = int(seconds)
    hours = total // 3600
    minutes = (total % 3600) // 60
    rem = total % 60
    if hours:
        return f"{hours:02d}:{minutes:02d}:{rem:02d}"
    return f"{minutes:02d}:{rem:02d}"


def load_repo_observations(repo_path: Path | None) -> dict[str, bool]:
    observations = {
        "repo_requires_openai_for_llm_steps": False,
        "repo_requires_hf_for_diarization": False,
        "transcribe_command_uses_openai": False,
    }
    if repo_path is None:
        return observations

    llm_path = repo_path / "src" / "interview_project_qa" / "llm.py"
    audio_path = repo_path / "src" / "interview_project_qa" / "audio.py"
    pipeline_path = repo_path / "src" / "interview_project_qa" / "pipeline.py"

    if llm_path.exists():
        llm_text = llm_path.read_text(encoding="utf-8")
        observations["repo_requires_openai_for_llm_steps"] = (
            "OPENAI_API_KEY is required for LLM steps." in llm_text
        )
    if audio_path.exists():
        audio_text = audio_path.read_text(encoding="utf-8")
        observations["repo_requires_hf_for_diarization"] = (
            "HF_TOKEN is required for pyannote diarization." in audio_text
        )
    if pipeline_path.exists():
        pipeline_text = pipeline_path.read_text(encoding="utf-8")
        observations["transcribe_command_uses_openai"] = (
            "assign_roles(role_input)" in pipeline_text
        )
    return observations


def build_report(args: argparse.Namespace) -> dict[str, object]:
    audio_path = Path(args.audio).expanduser()
    repo_path = resolve_repo(args.repo)
    observations = load_repo_observations(repo_path)

    ffmpeg_ok = shutil.which("ffmpeg") is not None
    ffprobe_ok = shutil.which("ffprobe") is not None

    env_present = {
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "HF_TOKEN": bool(os.getenv("HF_TOKEN")),
        "NOTION_API_TOKEN": bool(os.getenv("NOTION_API_TOKEN")),
        "NOTION_MCP_ACCESS_TOKEN": bool(os.getenv("NOTION_MCP_ACCESS_TOKEN")),
    }

    duration_seconds = probe_duration(audio_path) if audio_path.exists() else None

    full_missing: list[str] = []
    transcribe_missing: list[str] = []

    if repo_path is None:
        full_missing.append("repo checkout")
        transcribe_missing.append("repo checkout")
    if not audio_path.exists():
        full_missing.append("audio file")
        transcribe_missing.append("audio file")
    if not ffmpeg_ok:
        full_missing.append("ffmpeg")
        transcribe_missing.append("ffmpeg")
    if not ffprobe_ok:
        full_missing.append("ffprobe")
        transcribe_missing.append("ffprobe")
    if observations["repo_requires_hf_for_diarization"] and not env_present["HF_TOKEN"]:
        full_missing.append("HF_TOKEN")
        transcribe_missing.append("HF_TOKEN")
    if observations["repo_requires_openai_for_llm_steps"] and not env_present["OPENAI_API_KEY"]:
        full_missing.append("OPENAI_API_KEY")
    if observations["transcribe_command_uses_openai"] and not env_present["OPENAI_API_KEY"]:
        transcribe_missing.append("OPENAI_API_KEY")

    title = args.title
    hints = args.project_hints.strip()
    repo_text = str(repo_path) if repo_path else "<repo-path>"
    audio_text = str(audio_path)

    return {
        "repo_path": str(repo_path) if repo_path else None,
        "repo_found": repo_path is not None,
        "audio": {
            "path": audio_text,
            "exists": audio_path.exists(),
            "suffix": audio_path.suffix.lower(),
            "size_bytes": audio_path.stat().st_size if audio_path.exists() else None,
            "duration_seconds": duration_seconds,
            "duration_hms": format_duration(duration_seconds),
        },
        "binaries": {
            "ffmpeg": ffmpeg_ok,
            "ffprobe": ffprobe_ok,
        },
        "env_present": env_present,
        "code_observations": observations,
        "readiness": {
            "preflight_only": {
                "ready": audio_path.exists(),
                "missing": [] if audio_path.exists() else ["audio file"],
            },
            "repo_transcribe_command": {
                "ready": not transcribe_missing,
                "missing": transcribe_missing,
            },
            "repo_full_pipeline": {
                "ready": not full_missing,
                "missing": full_missing,
            },
        },
        "suggested_commands": {
            "preflight": (
                f"python scripts/preflight.py --repo \"{repo_text}\" --audio \"{audio_text}\""
            ),
            "repo_run": (
                f"interview-project-qa run --audio \"{audio_text}\" --title \"{title}\" "
                f"--project-hints \"{hints}\" --notion-mode local"
            ).strip(),
            "repo_transcribe": (
                f"interview-project-qa transcribe --audio \"{audio_text}\" --title \"{title}\" "
                f"--project-hints \"{hints}\""
            ).strip(),
        },
        "python_version": sys.version.split()[0],
    }


def print_summary(report: dict[str, object]) -> None:
    readiness = report["readiness"]
    audio = report["audio"]
    print("Interview-QA preflight")
    print(f"- Repo found: {report['repo_found']}")
    print(f"- Audio exists: {audio['exists']}")
    print(f"- Audio duration: {audio['duration_hms']}")
    print(f"- Full pipeline ready: {readiness['repo_full_pipeline']['ready']}")
    print(
        f"- Full pipeline missing: {', '.join(readiness['repo_full_pipeline']['missing']) or 'none'}"
    )
    print(
        f"- Repo transcribe ready: {readiness['repo_transcribe_command']['ready']}"
    )
    print(
        f"- Repo transcribe missing: {', '.join(readiness['repo_transcribe_command']['missing']) or 'none'}"
    )


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if not args.json_only:
        print_summary(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
