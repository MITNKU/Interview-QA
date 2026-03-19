from __future__ import annotations

from faster_whisper import WhisperModel

from .config import settings
from .models import AudioSegment


def build_whisper_model() -> WhisperModel:
    compute_type = None if settings.whisper_compute_type == "default" else settings.whisper_compute_type
    kwargs = {"device": settings.whisper_device}
    if compute_type:
        kwargs["compute_type"] = compute_type
    return WhisperModel(settings.whisper_model_size, **kwargs)


def transcribe_segments(items: list[tuple[str, str, float, float]]) -> list[AudioSegment]:
    model = build_whisper_model()
    results: list[AudioSegment] = []
    for speaker, seg_path, start, end in items:
        segments, _ = model.transcribe(seg_path, vad_filter=True, beam_size=5)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        if text:
            results.append(AudioSegment(speaker=speaker, start=start, end=end, text=text))
    return merge_transcribed_segments(results)


def merge_transcribed_segments(items: list[AudioSegment], max_gap: float = 1.2) -> list[AudioSegment]:
    if not items:
        return []
    merged = [items[0].model_copy(deep=True)]
    for item in items[1:]:
        last = merged[-1]
        if item.speaker == last.speaker and item.start - last.end <= max_gap:
            last.end = item.end
            last.text = f"{last.text} {item.text}".strip()
        else:
            merged.append(item.model_copy(deep=True))
    return merged
