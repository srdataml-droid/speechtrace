"""Small dependency-free tests of the explicit reference-relative rubric."""
from src.rubric import score_relative_delivery


def base():
    return {"events":[], "metrics":{"duration_ratio":1.0, "relative_energy_db":0.0}}


def test_identical_measurements_have_perfect_relative_similarity():
    x = score_relative_delivery(base())
    assert x["combined_reference_similarity"] == 100.0
    assert all(value == 100.0 for value in x["scores"].values())


def test_pause_penalty_is_local_to_pause_dimension():
    b=base()
    b["events"]=[{"type":"extra_pause", "delta":1.2}]
    a=score_relative_delivery(b)
    assert a["scores"]["pause"] < 100
    assert a["scores"]["relative_pace"] == 100
    assert a["scores"]["recording_level"] == 100


def test_level_difference_not_misinterpreted_as_pace():
    b=base()
    b["metrics"]["relative_energy_db"]=-8.0
    a=score_relative_delivery(b)
    assert a["scores"]["recording_level"] == 36.0
    assert a["scores"]["relative_pace"] == 100


def test_large_deviations_are_clipped():
    b=base()
    b["metrics"]["duration_ratio"]=2.0
    b["metrics"]["relative_energy_db"]=-25.0
    x=score_relative_delivery(b)
    assert x["scores"]["relative_pace"] == 0.0
    assert x["scores"]["recording_level"] == 0.0
