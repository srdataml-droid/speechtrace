"""End-to-end Gradio callback checks on the bundled synthetic fixtures."""
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import pytest

from legacy_comparison import ROOT, TRANSCRIPT, compare, demo


def test_gradio_blocks_can_build_configuration():
    config = demo.config
    assert config["components"]
    assert any(x["type"] == "audio" for x in config["components"])
    assert any(x["type"] == "plot" for x in config["components"])


def test_missing_recording_is_rejected():
    with pytest.raises(Exception, match="both a reference and a rehearsal"):
        compare(None, None, "test")


@pytest.mark.parametrize("sample,expected", [
    ("extra_pause", "extra_pause"),
    ("rushed", "duration_difference"),
    ("quiet", "energy_difference"),
])
def test_example_analysis_produces_shareable_outputs(sample, expected):
    ref = ROOT / "data" / "reference" / "ideal.wav"
    attempt = ROOT / "data" / "flawed" / f"{sample}.wav"
    summary, plot, table, details, report_file = compare(str(ref), str(attempt), TRANSCRIPT)
    assert "Comparison finished" in summary
    assert "not" in summary.lower()
    assert isinstance(plot, go.Figure)
    assert len(plot.data) == 4
    assert isinstance(table, pd.DataFrame)
    assert any(e["type"] == expected for e in details["events"])
    saved = json.loads(Path(report_file).read_text(encoding="utf-8"))
    assert saved["events"] == details["events"]
    Path(report_file).unlink()
