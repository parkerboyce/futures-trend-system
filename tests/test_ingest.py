from ft.data.ingest import _normalize_bars
import pandas as pd


def test_normalize_bars_sorts_and_dedupes():
    df = pd.DataFrame(
        {
            "ts_event": ["2024-01-01T00:01:00Z", "2024-01-01T00:00:00Z", "2024-01-01T00:00:00Z"],
            "open": [1, 1, 1],
            "high": [1, 1, 1],
            "low": [1, 1, 1],
            "close": [1, 1, 1],
            "volume": [10, 10, 10],
        }
    )
    out = _normalize_bars(df)
    assert out["ts_event"].is_monotonic_increasing
    assert out["ts_event"].nunique() == len(out)