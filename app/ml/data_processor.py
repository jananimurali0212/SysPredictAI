"""Historical system metrics data processing and feature engineering module."""
import logging
from datetime import datetime
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from app.database.db import Database, get_db

logger = logging.getLogger(__name__)


class DataProcessor:
    """Retrieves, cleans, sorts, and feature-engineers historical system metrics."""

    FEATURE_COLS = [
        "cpu_percent",
        "memory_percent",
        "cpu_lag_1",
        "cpu_lag_2",
        "cpu_lag_3",
        "cpu_lag_5",
        "memory_lag_1",
        "memory_lag_2",
        "memory_lag_3",
        "memory_lag_5",
        "cpu_roll_mean_1m",
        "cpu_roll_mean_5m",
        "cpu_roll_mean_15m",
        "memory_roll_mean_1m",
        "memory_roll_mean_5m",
        "memory_roll_mean_15m",
        "cpu_roll_std_5m",
        "memory_roll_std_5m",
        "cpu_trend",
        "memory_trend",
    ]

    def __init__(self, database: Optional[Database] = None):
        self.db = database or get_db()

    def fetch_historical_dataframe(
        self,
        limit: int = 2000,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Retrieve real metrics from database and return as a raw DataFrame."""
        df = self.db.get_history_df(limit=limit, start_time=start_time, end_time=end_time)
        return df

    def clean_and_sort(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean, deduplicate, and sort records chronologically.

        - Ensures valid timestamp column parsed as UTC datetime.
        - Sorts chronologically (oldest to newest).
        - Handles duplicate timestamps by keeping the most recent.
        - Fills or drops missing numeric values.
        """
        if df.empty:
            return df.copy()

        cleaned = df.copy()

        # Parse timestamp column
        if "timestamp" in cleaned.columns:
            cleaned["timestamp"] = pd.to_datetime(cleaned["timestamp"], utc=True, format="ISO8601")
            # Sort chronologically (ascending: past -> present)
            cleaned = cleaned.sort_values(by="timestamp", ascending=True)
            # Remove duplicate timestamps
            cleaned = cleaned.drop_duplicates(subset=["timestamp"], keep="last")

        # Cast expected numeric columns
        numeric_cols = [
            "cpu_percent",
            "memory_percent",
            "disk_percent",
            "upload_speed_bps",
            "download_speed_bps",
            "bytes_sent",
            "bytes_recv",
            "memory_used_bytes",
            "disk_used_bytes",
        ]
        for col in numeric_cols:
            if col in cleaned.columns:
                cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

        # Handle missing values: forward fill then backward fill, fallback to 0.0
        cleaned = cleaned.ffill().bfill().fillna(0.0)
        cleaned = cleaned.reset_index(drop=True)
        return cleaned

    def generate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate time-based, lag, rolling, and trend features from cleaned metric series.

        Features generated:
        - Current CPU and RAM metrics
        - Lag features (1, 2, 3, 5 steps)
        - 1-minute, 5-minute, and 15-minute rolling averages
        - Rolling standard deviations (volatility)
        - Utilization trends
        """
        if df.empty:
            return df.copy()

        data = self.clean_and_sort(df)
        if len(data) == 0:
            return data

        # Ensure timestamp is datetime and indexable
        data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, format="ISO8601")

        # 1. Current metric values
        if "cpu_percent" not in data.columns:
            data["cpu_percent"] = 0.0
        if "memory_percent" not in data.columns:
            data["memory_percent"] = 0.0

        # 2. Lag features (t-1, t-2, t-3, t-5)
        for lag in [1, 2, 3, 5]:
            data[f"cpu_lag_{lag}"] = data["cpu_percent"].shift(lag)
            data[f"memory_lag_{lag}"] = data["memory_percent"].shift(lag)

        # 3. Rolling averages and standard deviations using time-based windowing
        # When dataset is indexed by datetime, pandas supports rolling('1min'), rolling('5min'), rolling('15min')
        data_indexed = data.set_index("timestamp")

        # Rolling 1-minute (60s)
        roll_1m = data_indexed[["cpu_percent", "memory_percent"]].rolling("60s", min_periods=1).mean()
        data["cpu_roll_mean_1m"] = roll_1m["cpu_percent"].values
        data["memory_roll_mean_1m"] = roll_1m["memory_percent"].values

        # Rolling 5-minute (300s)
        roll_5m = data_indexed[["cpu_percent", "memory_percent"]].rolling("300s", min_periods=1).mean()
        data["cpu_roll_mean_5m"] = roll_5m["cpu_percent"].values
        data["memory_roll_mean_5m"] = roll_5m["memory_percent"].values

        # Rolling 15-minute (900s)
        roll_15m = data_indexed[["cpu_percent", "memory_percent"]].rolling("900s", min_periods=1).mean()
        data["cpu_roll_mean_15m"] = roll_15m["cpu_percent"].values
        data["memory_roll_mean_15m"] = roll_15m["memory_percent"].values

        # Rolling 5-minute standard deviation (volatility)
        roll_std_5m = data_indexed[["cpu_percent", "memory_percent"]].rolling("300s", min_periods=1).std()
        data["cpu_roll_std_5m"] = roll_std_5m["cpu_percent"].fillna(0.0).values
        data["memory_roll_std_5m"] = roll_std_5m["memory_percent"].fillna(0.0).values

        # 4. Recent utilization trend:
        # Difference between current value and 5-period moving average or step diff
        step_diff = min(5, len(data) - 1)
        if step_diff > 0:
            data["cpu_trend"] = data["cpu_percent"] - data["cpu_percent"].shift(step_diff)
            data["memory_trend"] = data["memory_percent"] - data["memory_percent"].shift(step_diff)
        else:
            data["cpu_trend"] = 0.0
            data["memory_trend"] = 0.0

        # Fill any NaNs created by shifts with backward fill then 0
        data = data.bfill().fillna(0.0)

        return data

    def prepare_training_data(
        self,
        df: pd.DataFrame,
        target_metric: str = "cpu_percent",
        horizon_steps: int = 1,
        forecast_horizon_steps: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare feature matrix X and target vector y for supervised ML training.

        The target is the metric value shifted by `horizon_steps` into the future.
        """
        steps = forecast_horizon_steps if forecast_horizon_steps is not None else horizon_steps
        featured_df = self.generate_features(df)
        if len(featured_df) <= steps:
            return pd.DataFrame(), pd.Series(dtype=float)

        available_features = [col for col in self.FEATURE_COLS if col in featured_df.columns]
        X = featured_df[available_features].iloc[:-steps].copy()
        y = featured_df[target_metric].shift(-steps).dropna()

        # Align indices
        common_len = min(len(X), len(y))
        return X.iloc[:common_len], y.iloc[:common_len]

    prepare_ml_dataset = prepare_training_data
