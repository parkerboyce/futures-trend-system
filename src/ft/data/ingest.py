from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import databento as db

from ft.config.loader import get_env
from ft.data.storage import save_parquet


REQUIRED_COLS = ["ts_event", "open", "high", "low", "close", "volume"]


@dataclass(frozen=True)
class DatabentoSpec:
    dataset: str
    schema: str
    stype_in: str


def _normalize_bars(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Got columns={list(df.columns)}")

    out = df[REQUIRED_COLS].copy()
    out["ts_event"] = pd.to_datetime(out["ts_event"], utc=True)
    out = out.sort_values("ts_event").drop_duplicates(subset=["ts_event"])
    return out.reset_index(drop=True)


def download_contract_ohlcv(
    *,
    symbol: str,
    contract: str,
    start: str,
    end: str,
    raw_dir: str | Path,
    spec: DatabentoSpec,
    api_key_env: str = "DATABENTO_API_KEY",
) -> Path:
    """
    Download OHLCV bars for a single futures contract and save as Parquet.
    `contract` should be the Databento symbology you plan to use (e.g., raw symbol).
    """
    api_key = get_env(api_key_env)
    client = db.Historical(api_key)

    # Databento returns a Databento data object; convert to pandas
    data = client.timeseries.get_range(
        dataset=spec.dataset,
        schema=spec.schema,
        stype_in=spec.stype_in,
        symbols=[contract],
        start=start,
        end=end,
    )
    df = data.to_df()

    df = _normalize_bars(df)

    out_path = Path(raw_dir) / symbol / f"{contract}.parquet"
    save_parquet(df, out_path)
    return out_path