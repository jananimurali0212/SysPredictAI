"""Pydantic schemas for Machine Learning forecasting, anomaly detection, and risk assessment."""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ForecastPoint(BaseModel):
    """A single predicted resource utilization point in time."""
    horizon_seconds: int = Field(..., description="Seconds into the future")
    target_timestamp: datetime = Field(..., description="Target predicted timestamp")
    predicted_value: float = Field(..., ge=0.0, le=100.0, description="Predicted utilization percentage (0-100)")
    lower_bound: Optional[float] = Field(None, ge=0.0, le=100.0, description="Estimated lower bound")
    upper_bound: Optional[float] = Field(None, ge=0.0, le=100.0, description="Estimated upper bound")


class ModelEvaluation(BaseModel):
    """Performance metrics comparing trained model against baseline."""
    model_mae: float = Field(..., description="Mean Absolute Error of the trained model")
    model_rmse: float = Field(..., description="Root Mean Squared Error of the trained model")
    baseline_mae: float = Field(..., description="Mean Absolute Error of the baseline model")
    baseline_rmse: float = Field(..., description="Root Mean Squared Error of the baseline model")
    mae_improvement_percent: Optional[float] = Field(None, description="Percentage MAE improvement over baseline")
    rmse_improvement_percent: Optional[float] = Field(None, description="Percentage RMSE improvement over baseline")


class ModelMetadata(BaseModel):
    """Metadata describing the trained model artifact."""
    model_type: str = Field(..., description="Algorithm name (e.g., RandomForestRegressor)")
    trained_at: datetime = Field(..., description="Timestamp when model was trained")
    training_samples: int = Field(..., description="Number of historical samples used for training")
    test_samples: int = Field(..., description="Number of chronological samples used for testing")
    features_used: List[str] = Field(..., description="List of feature column names")
    parameters: Dict[str, str] = Field(default_factory=dict, description="Model hyperparameters")


class PredictionResponse(BaseModel):
    """Structured response for CPU or RAM forecasting."""
    metric: str = Field(..., description="Target metric ('cpu' or 'memory')")
    status: str = Field(..., description="'success', 'insufficient_data', or 'error'")
    message: str = Field(..., description="Descriptive status message")
    timestamp: datetime = Field(..., description="UTC timestamp of the forecast generation")
    current_value: Optional[float] = Field(None, ge=0.0, le=100.0, description="Latest observed value")
    method_used: str = Field(..., description="'random_forest', 'baseline_moving_average', or 'none'")
    predictions: List[ForecastPoint] = Field(default_factory=list, description="Future forecasted points")
    evaluation: Optional[ModelEvaluation] = Field(None, description="Model performance metrics if trained")
    model_metadata: Optional[ModelMetadata] = Field(None, description="Metadata of the active model")


class PredictionSummary(BaseModel):
    """Aggregated prediction summary covering CPU, Memory, and predictive insights."""
    timestamp: datetime = Field(..., description="UTC timestamp of the summary")
    status: str = Field(..., description="Overall prediction pipeline status")
    cpu_forecast: PredictionResponse = Field(..., description="CPU utilization forecast")
    memory_forecast: PredictionResponse = Field(..., description="Memory utilization forecast")
    summary: str = Field(..., description="Synthesized executive summary of upcoming resource pressure")


class AnomalyItem(BaseModel):
    """Single detected anomaly entry."""
    anomaly_id: str = Field(..., description="Unique anomaly identifier")
    timestamp: datetime = Field(..., description="Timestamp of the anomalous metric event")
    metric_name: str = Field(..., description="Hardware or network metric ('cpu', 'memory', 'disk', 'network')")
    observed_value: float = Field(..., description="Observed value that triggered the anomaly")
    threshold_or_baseline: Optional[float] = Field(None, description="Relevant threshold or baseline value")
    anomaly_score: Optional[float] = Field(None, description="Anomaly severity score / decision function score")
    detection_method: str = Field(..., description="Detection technique ('rule_based' or 'isolation_forest')")
    severity: str = Field(..., description="Severity level: 'Low', 'Medium', 'High', or 'Critical'")
    explanation: str = Field(..., description="Concise explanation of the anomaly")
    recommended_action: str = Field(..., description="Actionable next step recommendation")


class AnomalyDetectionResponse(BaseModel):
    """Structured response for detected system anomalies."""
    timestamp: datetime = Field(..., description="UTC timestamp of analysis")
    total_anomalies: int = Field(..., description="Count of active anomalies")
    isolation_forest_enabled: bool = Field(..., description="Whether Isolation Forest was fitted and evaluated")
    anomalies: List[AnomalyItem] = Field(default_factory=list, description="List of detected anomalies")


class RiskBreakdown(BaseModel):
    """Component-specific risk analysis details."""
    cpu_status: str = Field(..., description="CPU risk contribution ('Normal', 'Warning', 'High Risk', 'Critical')")
    memory_status: str = Field(..., description="Memory risk contribution")
    disk_status: str = Field(..., description="Disk risk contribution")
    network_status: str = Field(..., description="Network risk contribution")
    forecast_risk: str = Field(..., description="Forward-looking risk from ML projections")
    trend_description: str = Field(..., description="Trend description (e.g. CPU rising +4.2% over 5m)")


class PredictiveRiskResponse(BaseModel):
    """Complete predictive risk assessment output."""
    timestamp: datetime = Field(..., description="UTC timestamp of the risk assessment")
    risk_status: str = Field(..., description="'Normal', 'Warning', 'High Risk', or 'Critical'")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Composite numeric risk score from 0 to 100")
    current_cpu_percent: float = Field(..., ge=0.0, le=100.0, description="Current CPU utilization")
    current_memory_percent: float = Field(..., ge=0.0, le=100.0, description="Current RAM utilization")
    recent_cpu_trend: str = Field(..., description="Recent trend direction: 'rising', 'declining', or 'stable'")
    recent_memory_trend: str = Field(..., description="Recent trend direction: 'rising', 'declining', or 'stable'")
    breakdown: RiskBreakdown = Field(..., description="Component risk breakdown")
    active_anomalies_count: int = Field(..., description="Number of currently active anomalies")
    recommendations: List[str] = Field(default_factory=list, description="Prioritized recommendations")

