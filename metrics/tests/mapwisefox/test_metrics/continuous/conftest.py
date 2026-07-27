import pytest


@pytest.fixture
def rating_records():
    return [
        {"id": "a", "score": 1.0},
        {"id": "b", "score": 2.0},
        {"id": "c", "score": 3.0},
    ]


@pytest.fixture
def trusted_files(tmp_path, csv_file, rating_records):
    r1 = [{"id": r["id"], "score": r["score"]} for r in rating_records]
    r2 = [{"id": r["id"], "score": r["score"] + 0.5} for r in rating_records]
    return [
        csv_file(r1, "rater_a.csv"),
        csv_file(r2, "rater_b.csv"),
    ]


@pytest.fixture
def evaluated_file(tmp_path, csv_file, rating_records):
    return csv_file(
        [{"id": r["id"], "score": r["score"]} for r in rating_records],
        "evaluated.csv",
    )
