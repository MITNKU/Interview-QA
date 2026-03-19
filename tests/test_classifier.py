from interview_project_qa.classifier import shortlist_project_question_windows


def test_shortlist_project_question_windows() -> None:
    dialogue = [
        {"role": "interviewer", "speaker": "A", "start": 0.0, "end": 3.0, "text": "你在推荐系统项目里主要负责什么？"},
        {"role": "candidate", "speaker": "B", "start": 3.1, "end": 10.0, "text": "我负责排序和特征工程。"},
        {"role": "interviewer", "speaker": "A", "start": 10.5, "end": 12.0, "text": "你的职业规划是什么？"},
        {"role": "candidate", "speaker": "B", "start": 12.1, "end": 15.0, "text": "我希望继续做基础架构。"},
    ]
    windows = shortlist_project_question_windows(dialogue, ["推荐系统"])
    assert len(windows) == 1
    assert windows[0].project_hint_hits == ["推荐系统"]
