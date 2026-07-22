import pandas as pd

from mapwisefox.assistant.judge._study_qa import _fill_results

CRITERIA = [{"label": "re1", "category": "reporting", "question": "Is it formal?"}]


def _df_with_float_column():
    df = pd.DataFrame([{"title": "T1"}])
    df["re1"] = pd.array([None], dtype="Float64")
    return df


def test_fill_results_writes_numeric_score():
    df = _df_with_float_column()
    results = {0: {"re1": {"score": 8, "reason": "good"}}}

    out = _fill_results(df, CRITERIA, results)

    assert out.loc[0, "re1"] == 8


def test_fill_results_leaves_score_empty_when_unscored():
    df = _df_with_float_column()
    results = {
        0: {
            "re1": {
                "score": None,
                "reason": "left unscored: LLM did not return a usable score",
            }
        }
    }

    out = _fill_results(df, CRITERIA, results)

    assert pd.isna(out.loc[0, "re1"])


def test_fill_results_still_records_reason_when_unscored():
    df = _df_with_float_column()
    results = {
        0: {
            "re1": {
                "score": None,
                "reason": "left unscored: LLM did not return a usable score",
            }
        }
    }

    out = _fill_results(df, CRITERIA, results)

    assert "left unscored" in out.loc[0, "evaluation"]
