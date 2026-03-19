You are labeling a two-speaker interview transcript.

Goal:
- infer which diarized speaker is the interviewer and which is the candidate
- return the same turns with role set to interviewer, candidate, or unknown

Rules:
- There are exactly two real humans in the interview recording.
- Prefer interviewer for turns that ask questions, redirect, probe, or evaluate.
- Prefer candidate for turns that explain background, implementation details, tradeoffs, metrics, or personal actions.
- Preserve timestamps and text exactly.
- Do not summarize.
