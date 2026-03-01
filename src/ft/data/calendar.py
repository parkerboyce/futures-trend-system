from __future__ import annotations

import pandas as pd


def to_ny(ts: pd.Series) -> pd.Series:
    # ts is UTC datetime64[ns, UTC]
    return ts.dt.tz_convert("America/New_York")


def filter_rth(df: pd.DataFrame, start_hhmm: str = "09:30", end_hhmm: str = "16:00") -> pd.DataFrame:
    """
    Keep bars whose NY time is within [start, end).
    Assumes ts_event is tz-aware UTC.
    """
    if "ts_event" not in df.columns:
        raise ValueError("df must contain ts_event")

    ts_ny = to_ny(df["ts_event"])
    t = ts_ny.dt.time

    start = pd.to_datetime(start_hhmm).time()
    end = pd.to_datetime(end_hhmm).time()

    mask = (t >= start) & (t < end)
    return df.loc[mask].reset_index(drop=True)