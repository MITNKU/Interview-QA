from __future__ import annotations

from pathlib import Path

from pyannote.audio import Pipeline

from .config import settings
from .utils import ensure_dir, ffmpeg_extract, ffmpeg_normalize, ffprobe_duration


def normalize_audio(input_audio: Path, work_dir: Path) -> Path:
    ensure_dir(work_dir)
    normalized = work_dir / "normalized.wav"
    ffmpeg_normalize(input_audio, normalized)
    return normalized


def diarize_two_speakers(audio_path: Path) -> list[tuple[str, float, float]]:
    if not settings.hf_token:
        raise RuntimeError("HF_TOKEN is required for pyannote diarization.")

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization",
        use_auth_token=settings.hf_token,
    )
    diarization = pipeline(str(audio_path), num_speakers=2)

    segments: list[tuple[str, float, float]] = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append((speaker, float(turn.start), float(turn.end)))
    return merge_diarized_segments(segments)


def merge_diarized_segments(
    diarized: list[tuple[str, float, float]],
    max_gap: float | None = None,
    max_duration: float | None = None,
) -> list[tuple[str, float, float]]:
    if not diarized:
        return []
    max_gap = settings.diarization_gap_seconds if max_gap is None else max_gap
    max_duration = settings.max_merged_speaker_seconds if max_duration is None else max_duration

    merged: list[list[object]] = [[diarized[0][0], diarized[0][1], diarized[0][2]]]
    for speaker, start, end in diarized[1:]:
        last = merged[-1]
        last_speaker = str(last[0])
        last_start = float(last[1])
        last_end = float(last[2])
        same_speaker = speaker == last_speaker
        small_gap = start - last_end <= max_gap
        under_limit = end - last_start <= max_duration
        if same_speaker and small_gap and under_limit:
            last[2] = end
        else:
            merged.append([speaker, start, end])
    return [(str(s), float(a), float(b)) for s, a, b in merged if float(b) > float(a)]


def slice_segments(source_audio: Path, diarized: list[tuple[str, float, float]], work_dir: Path) -> list[tuple[str, Path, float, float]]:
    segment_dir = ensure_dir(work_dir / "speaker_segments")
    total_duration = ffprobe_duration(source_audio)
    padding = settings.diarization_padding_seconds
    max_len = settings.max_transcribe_chunk_seconds
    result: list[tuple[str, Path, float, float]] = []
    seg_index = 0

    for speaker, start, end in diarized:
        cur = start
        while cur < end:
            chunk_end = min(cur + max_len, end)
            padded_start = max(0.0, cur - padding)
            padded_end = min(total_duration, chunk_end + padding)
            seg_path = segment_dir / f"seg_{seg_index:05d}_{speaker}.wav"
            ffmpeg_extract(source_audio, seg_path, padded_start, padded_end)
            result.append((speaker, seg_path, padded_start, padded_end))
            seg_index += 1
            cur = chunk_end
    return result
