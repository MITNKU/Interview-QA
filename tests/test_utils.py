from interview_project_qa.utils import chunked, seconds_to_mmss, slugify


def test_slugify() -> None:
    assert slugify("推荐系统 重排项目")


def test_seconds_to_mmss() -> None:
    assert seconds_to_mmss(65) == "01:05"


def test_chunked() -> None:
    assert chunked([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
