"""Pydantic schemas for Gemini-powered system diagnostics and AI insights."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AIInsightQueryRequest(BaseModel):
    """Payload for user querying Gemini AI about system state."""
    question: str = Field(..., min_length=2, max_length=500, description="User question about system performance")


class AIInsightResponse(BaseModel):
    """Structured response containing AI diagnostic analysis."""
    question: str = Field(..., description="The analyzed question")
    analysis: str = Field(..., description="Synthesized diagnostic narrative")
    observed_facts: List[str] = Field(default_factory=list, description="Directly observed metrics and telemetry facts")
    possible_causes: List[str] = Field(default_factory=list, description="Plausible technical root causes")
    recommended_actions: List[str] = Field(default_factory=list, description="Prioritized recommendations to resolve or optimize")
    source: str = Field(..., description="'gemini_api' or 'grounded_telemetry_engine'")
    gemini_configured: bool = Field(..., description="True if GEMINI_API_KEY is active and responding")
    timestamp: datetime = Field(..., description="UTC timestamp of the generation")


class AISummaryResponse(BaseModel):
    """Concise system health summary for the Overview dashboard."""
    headline: str = Field(..., description="High-level system health status statement")
    summary: str = Field(..., description="Paragraph summarizing current performance and predictive state")
    health_level: str = Field(..., description="'healthy', 'warning', 'critical'")
    active_concerns_count: int = Field(..., description="Number of detected anomalies or critical metrics")
    key_recommendation: str = Field(..., description="Single most urgent recommended action")
    source: str = Field(..., description="'gemini_api' or 'grounded_telemetry_engine'")
    timestamp: datetime = Field(..., description="UTC timestamp of the summary")
