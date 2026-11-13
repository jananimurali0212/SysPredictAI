"""Machine learning resource forecasting engine using Random Forest Regressor and baseline models."""
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from app.config import settings
from app.ml.data_processor import DataProcessor
from app.schemas.analytics import (
    ForecastPoint,
    ModelEvaluation,
    ModelMetadata,
    PredictionResponse,
    PredictionSummary,
)

logger = logging.getLogger(__name__)


class ResourceForecaster:
    """Forecasting service providing baseline and Random Forest resource predictions."""

    def __init__(
        self,
        data_processor: Optional[DataProcessor] = None,
        min_samples: Optional[int] = None,
        model_dir: Optional[str] = None,
    ):
        self.processor = data_processor or DataProcessor()
        self.min_samples = min_samples or settings.ML_MIN_TRAINING_SAMPLES
        self.model_dir = Path(model_dir or settings.MODEL_DIR)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self._models: Dict[str, RandomForestRegressor] = {}
        self._metadata: Dict[str, ModelMetadata] = {}
        self._evaluations: Dict[str, ModelEvaluation] = {}

    def _get_model_path(self, metric: str) -> Path:
        return self.model_dir / f"{metric}_rf_model.joblib"

    def _get_meta_path(self, metric: str) -> Path:
        return self.model_dir / f"{metric}_metadata.json"

    def _evaluate_baseline(
        self,
        y_train: pd.Series,
        y_test: pd.Series,
        window: int = 5,
    ) -> Tuple[float, float]:
        """Compute MAE and RMSE for moving average baseline on test split."""
        if len(y_test) == 0:
            return 0.0, 0.0

        # Baseline: Moving average of recent observations
        recent_values = list(y_train.iloc[-window:].values) if len(y_train) >= window else list(y_train.values)
        if not recent_values:
            recent_values = [0.0]

        baseline_preds = []
        for actual in y_test:
            pred = float(np.mean(recent_values))
            baseline_preds.append(pred)
            recent_values.append(actual)
            if len(recent_values) > window:
                recent_values.pop(0)

        mae = float(mean_absolute_error(y_test, baseline_preds))
        rmse = float(root_mean_squared_error(y_test, baseline_preds))
        return mae, rmse

    def train_model(
        self,
        raw_df: pd.DataFrame,
        metric: str = "cpu",
    ) -> Tuple[Optional[RandomForestRegressor], Optional[ModelEvaluation], Optional[ModelMetadata]]:
        """Train Random Forest regressor with chronological train/test split.

        Args:
            raw_df: Historical dataframe of collected metrics.
            metric: 'cpu' or 'memory'.
        """
        target_col = "cpu_percent" if metric == "cpu" else "memory_percent"

        featured_df = self.processor.generate_features(raw_df)
        if len(featured_df) < self.min_samples:
            logger.info(
                "Insufficient historical samples for %s model training (have %d, require %d)",
                metric,
                len(featured_df),
                self.min_samples,
            )
            return None, None, None

        # Build training set (1-step forward forecast)
        X, y = self.processor.prepare_ml_dataset(featured_df, target_metric=target_col, horizon_steps=1)
        if len(X) < self.min_samples:
            return None, None, None

        # Chronological train/test split (no random shuffling for time-series)
        split_idx = int(len(X) * 0.8)
        # Ensure at least 5 test points
        split_idx = min(split_idx, len(X) - 5)
        if split_idx <= 0:
            split_idx = int(len(X) * 0.8)

        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        if len(X_train) == 0 or len(X_test) == 0:
            return None, None, None

        # Baseline performance
        baseline_mae, baseline_rmse = self._evaluate_baseline(y_train, y_test)

        # Train Random Forest Regressor
        rf = RandomForestRegressor(
            n_estimators=50,
            max_depth=6,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=1,
        )
        rf.fit(X_train, y_train)

        # Evaluate on test set
        y_pred_test = rf.predict(X_test)
        # Clip test predictions to 0-100
        y_pred_test = np.clip(y_pred_test, 0.0, 100.0)

        model_mae = float(mean_absolute_error(y_test, y_pred_test))
        model_rmse = float(root_mean_squared_error(y_test, y_pred_test))

        mae_improvement = (
            round(((baseline_mae - model_mae) / baseline_mae) * 100, 2)
            if baseline_mae > 0.0
            else 0.0
        )
        rmse_improvement = (
            round(((baseline_rmse - model_rmse) / baseline_rmse) * 100, 2)
            if baseline_rmse > 0.0
            else 0.0
        )

        evaluation = ModelEvaluation(
            model_mae=round(model_mae, 3),
            model_rmse=round(model_rmse, 3),
            baseline_mae=round(baseline_mae, 3),
            baseline_rmse=round(baseline_rmse, 3),
            mae_improvement_percent=mae_improvement,
            rmse_improvement_percent=rmse_improvement,
        )

        metadata = ModelMetadata(
            model_type="RandomForestRegressor",
            trained_at=datetime.now(timezone.utc),
            training_samples=len(X_train),
            test_samples=len(X_test),
            features_used=list(X.columns),
            parameters={
                "n_estimators": "50",
                "max_depth": "6",
                "min_samples_split": "4",
                "min_samples_leaf": "2",
            },
        )

        # Cache in-memory
        self._models[metric] = rf
        self._metadata[metric] = metadata
        self._evaluations[metric] = evaluation

        # Persist to disk
        try:
            joblib.dump(rf, self._get_model_path(metric))
            with open(self._get_meta_path(metric), "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "metadata": metadata.model_dump(mode="json"),
                        "evaluation": evaluation.model_dump(mode="json"),
                    },
                    f,
                    indent=2,
                )
            logger.info("Persisted %s Random Forest model and metadata to %s", metric, self.model_dir)
        except Exception as save_err:
            logger.warning("Could not persist model artifact: %s", save_err)

        return rf, evaluation, metadata

    def forecast_metric(
        self,
        raw_df: pd.DataFrame,
        metric: str = "cpu",
        horizons_seconds: Optional[List[int]] = None,
    ) -> PredictionResponse:
        """Generate forecasts for future intervals using real historical metrics.

        Handles insufficient data gracefully.
        Clips predictions to valid bounds [0.0, 100.0].
        """
        horizons = horizons_seconds or [60, 300, 900]
        now = datetime.now(timezone.utc)
        target_col = "cpu_percent" if metric == "cpu" else "memory_percent"

        # Check raw records
        if raw_df.empty or len(raw_df) == 0:
            return PredictionResponse(
                metric=metric,
                status="insufficient_data",
                message="Insufficient historical data for reliable forecasting. Minimum required samples: "
                + str(self.min_samples),
                timestamp=now,
                current_value=None,
                method_used="none",
                predictions=[],
                evaluation=None,
                model_metadata=None,
            )

        featured_df = self.processor.generate_features(raw_df)
        samples_count = len(featured_df)
        latest_row = featured_df.iloc[-1]
        current_val = round(float(latest_row[target_col]), 2) if target_col in latest_row else 0.0

        # Insufficient data check
        if samples_count < self.min_samples:
            return PredictionResponse(
                metric=metric,
                status="insufficient_data",
                message=f"Insufficient historical data for reliable forecasting ({samples_count}/{self.min_samples} required records collected so far).",
                timestamp=now,
                current_value=current_val,
                method_used="none",
                predictions=[],
                evaluation=None,
                model_metadata=None,
            )

        # Train or retrieve trained model
        rf_model = self._models.get(metric)
        evaluation = self._evaluations.get(metric)
        metadata = self._metadata.get(metric)

        if rf_model is None:
            rf_model, evaluation, metadata = self.train_model(raw_df, metric=metric)

        if rf_model is None:
            # Fallback to moving average baseline if model fitting had insufficient samples
            return PredictionResponse(
                metric=metric,
                status="insufficient_data",
                message="Insufficient historical data for reliable forecasting.",
                timestamp=now,
                current_value=current_val,
                method_used="none",
                predictions=[],
                evaluation=None,
                model_metadata=None,
            )

        # Feature matrix for the latest state
        available_features = [col for col in self.processor.FEATURE_COLS if col in featured_df.columns]
        latest_X = featured_df[available_features].iloc[[-1]].copy()

        # Generate multi-horizon predictions
        # For multiple horizons: estimate trajectory using model output and recent trend
        base_pred = float(rf_model.predict(latest_X)[0])
        base_pred = float(np.clip(base_pred, 0.0, 100.0))

        # Recent trend factor per minute
        trend_col = "cpu_trend" if metric == "cpu" else "memory_trend"
        trend_rate = float(latest_row.get(trend_col, 0.0))

        # Confidence margin based on model RMSE
        margin = float(evaluation.model_rmse if evaluation else 3.0)

        predictions: List[ForecastPoint] = []
        for h in horizons:
            minutes_ahead = h / 60.0
            # Dampened trend projection over horizon
            dampened_trend = trend_rate * (1.0 - np.exp(-minutes_ahead / 5.0))
            projected = base_pred + (dampened_trend * 0.5)
            projected_clipped = round(float(np.clip(projected, 0.0, 100.0)), 2)

            lower = round(float(np.clip(projected_clipped - margin, 0.0, 100.0)), 2)
            upper = round(float(np.clip(projected_clipped + margin, 0.0, 100.0)), 2)

            target_time = now + timedelta(seconds=h)
            predictions.append(
                ForecastPoint(
                    horizon_seconds=h,
                    target_timestamp=target_time,
                    predicted_value=projected_clipped,
                    lower_bound=lower,
                    upper_bound=upper,
                )
            )

        return PredictionResponse(
            metric=metric,
            status="success",
            message="Resource forecast generated successfully using Random Forest Regressor.",
            timestamp=now,
            current_value=current_val,
            method_used="random_forest",
            predictions=predictions,
            evaluation=evaluation,
            model_metadata=metadata,
        )

    def forecast_summary(self, raw_df: pd.DataFrame) -> PredictionSummary:
        """Synthesize overall prediction summary across CPU and Memory."""
        now = datetime.now(timezone.utc)
        cpu_forecast = self.forecast_metric(raw_df, metric="cpu")
        mem_forecast = self.forecast_metric(raw_df, metric="memory")

        status = "success" if (cpu_forecast.status == "success" and mem_forecast.status == "success") else "partial"
        if cpu_forecast.status == "insufficient_data" and mem_forecast.status == "insufficient_data":
            status = "insufficient_data"

        # Generate human-readable summary
        insights = []
        if cpu_forecast.status == "success" and cpu_forecast.predictions:
            next_cpu = cpu_forecast.predictions[0].predicted_value
            insights.append(f"CPU forecast: {next_cpu}% utilization expected in 60s.")
        else:
            insights.append("CPU: Insufficient historical data for reliable forecasting.")

        if mem_forecast.status == "success" and mem_forecast.predictions:
            next_mem = mem_forecast.predictions[0].predicted_value
            insights.append(f"Memory forecast: {next_mem}% utilization expected in 60s.")
        else:
            insights.append("Memory: Insufficient historical data for reliable forecasting.")

        summary_text = " ".join(insights)

        return PredictionSummary(
            timestamp=now,
            status=status,
            cpu_forecast=cpu_forecast,
            memory_forecast=mem_forecast,
            summary=summary_text,
        )
