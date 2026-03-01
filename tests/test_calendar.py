import pandas as pd

from ft.data.calendar import filter_rth


def test_filter_rth_keeps_only_rth():
    df = pd.DataFrame(
        {
            "ts_event": pd.to_datetime(
                [
                    "2024-01-02T14:00:00Z",  # 09:00 ET (out)
                    "2024-01-02T14:35:00Z",  # 09:35 ET (in)
                    "2024-01-02T21:00:00Z",  # 16:00 ET (out, end exclusive)
                ],
                utc=True,
            ),
            "open": [1, 1, 1],
            "high": [1, 1, 1],
            "low": [1, 1, 1],
            "close": [1, 1, 1],
            "volume": [1, 1, 1],
        }
    )
    out = filter_rth(df)
    assert len(out) == 1