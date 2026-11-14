"""AI insights service leveraging Google Gemini API with intelligent local telemetry reasoning fallback."""
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config import settings
from app.schemas.ai import AIInsightResponse, AISummaryResponse

logger = logging.getLogger(__name__)


class AIService:
    """Provides grounded AI diagnostics for system metrics using Gemini or telemetry heuristics."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name or settings.GEMINI_MODEL
        self._gemini_client = None
        self._init_gemini()

    def _init_gemini(self) -> None:
        """Initialize Google Gemini client if API key is present."""
        if not self.api_key:
            logger.info("Gemini API key not configured. Operating in telemetry-grounded local reasoning mode.")
            return

        try:
            # Try new google.genai SDK first
            from google import genai
            self._gemini_client = genai.Client(api_key=self.api_key)
            logger.info("Initialized Google GenAI client with model %s", self.model_name)
        except Exception as e1:
            try:
                # Fallback to google.generativeai if genai is not configured
                import google.generativeai as gai
                gai.configure(api_key=self.api_key)
                self._gemini_client = gai.GenerativeModel(self.model_name)
                logger.info("Initialized google.generativeai client with model %s", self.model_name)
            except Exception as e2:
                logger.warning("Could not initialize Gemini SDK (%s, %s). Using local telemetry engine.", e1, e2)
                self._gemini_client = None

    def is_configured(self) -> bool:
        """Return True if Gemini API client is initialized and ready."""
        return self._gemini_client is not None and bool(self.api_key)

    def _build_context_summary(
        self,
        current_metrics: Any,
        top_processes: List[Any],
        anomalies: List[Any],
        risk_resp: Any,
        cpu_prediction: Any,
    ) -> Dict[str, Any]:
        """Distill safe, relevant system telemetry into structured context."""
        procs_data = []
        for p in top_processes[:6]:
            procs_data.append({
                "pid": getattr(p, "pid", 0),
                "name": getattr(p, "name", "unknown"),
                "cpu_percent": getattr(p, "cpu_percent", 0.0),
                "memory_percent": getattr(p, "memory_percent", 0.0),
            })

        anom_data = []
        for a in anomalies[:5]:
            anom_data.append({
                "metric": getattr(a, "metric_name", "unknown"),
                "severity": getattr(a, "severity", "Normal"),
                "observed_value": getattr(a, "observed_value", 0.0),
                "explanation": getattr(a, "explanation", ""),
            })

        forecast_info = "Insufficient data"
        if cpu_prediction and getattr(cpu_prediction, "predictions", None):
            pts = getattr(cpu_prediction, "predictions", [])
            if pts:
                forecast_info = f"Projected {pts[0].predicted_value}% in {pts[0].horizon_seconds}s"

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu_utilization_percent": getattr(current_metrics.cpu, "utilization_percent", 0.0) if current_metrics else 0.0,
            "logical_cores": getattr(current_metrics.cpu, "core_count_logical", 1) if current_metrics else 1,
            "memory_utilization_percent": getattr(current_metrics.memory, "utilization_percent", 0.0) if current_metrics else 0.0,
            "memory_used_gb": round(getattr(current_metrics.memory, "used_bytes", 0) / (1024**3), 2) if current_metrics else 0.0,
            "memory_total_gb": round(getattr(current_metrics.memory, "total_bytes", 0) / (1024**3), 2) if current_metrics else 0.0,
            "disk_utilization_percent": getattr(current_metrics.disk, "utilization_percent", 0.0) if current_metrics else 0.0,
            "upload_speed_kbps": round(getattr(current_metrics.network, "upload_speed_bps", 0.0) / 1024.0, 1) if current_metrics else 0.0,
            "download_speed_kbps": round(getattr(current_metrics.network, "download_speed_bps", 0.0) / 1024.0, 1) if current_metrics else 0.0,
            "top_processes": procs_data,
            "active_anomalies": anom_data,
            "risk_status": getattr(risk_resp, "risk_status", "Normal") if risk_resp else "Normal",
            "risk_score": getattr(risk_resp, "risk_score", 0.0) if risk_resp else 0.0,
            "cpu_trend": getattr(risk_resp, "recent_cpu_trend", "stable") if risk_resp else "stable",
            "memory_trend": getattr(risk_resp, "recent_memory_trend", "stable") if risk_resp else "stable",
            "cpu_forecast": forecast_info,
        }

    async def answer_question(
        self,
        question: str,
        current_metrics: Any,
        top_processes: List[Any],
        anomalies: List[Any],
        risk_resp: Any,
        cpu_prediction: Any,
    ) -> AIInsightResponse:
        """Answer user questions about host telemetry, using Gemini API or grounded telemetry reasoning."""
        now = datetime.now(timezone.utc)
        context = self._build_context_summary(
            current_metrics=current_metrics,
            top_processes=top_processes,
            anomalies=anomalies,
            risk_resp=risk_resp,
            cpu_prediction=cpu_prediction,
        )

        # Attempt Gemini generative call if configured
        if self.is_configured():
            try:
                gemini_resp = await self._call_gemini_api(question, context)
                if gemini_resp:
                    return AIInsightResponse(
                        question=question,
                        analysis=gemini_resp.get("analysis", "Analysis completed."),
                        observed_facts=gemini_resp.get("observed_facts", []),
                        possible_causes=gemini_resp.get("possible_causes", []),
                        recommended_actions=gemini_resp.get("recommended_actions", []),
                        source="gemini_api",
                        gemini_configured=True,
                        timestamp=now,
                    )
            except Exception as e:
                logger.warning("Gemini API call failed (%s); reverting to telemetry reasoning engine.", e)

        # Grounded telemetry reasoning engine fallback
        fallback = self._local_reasoning(question, context)
        return AIInsightResponse(
            question=question,
            analysis=fallback["analysis"],
            observed_facts=fallback["observed_facts"],
            possible_causes=fallback["possible_causes"],
            recommended_actions=fallback["recommended_actions"],
            source="grounded_telemetry_engine",
            gemini_configured=self.is_configured(),
            timestamp=now,
        )

    async def _call_gemini_api(self, question: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Query Gemini API with strict structured system prompt."""
        system_prompt = f"""You are SysPredictAI's Chief Diagnostic System Architect.
You must analyze the user's host system question based strictly on the provided real-time telemetry context.

TELEMETRY CONTEXT:
{json.dumps(context, indent=2)}

INSTRUCTIONS:
1. Clearly distinguish directly observed metric facts from plausible technical causes.
2. Provide concrete, prioritized recommended next steps.
3. Respond ONLY with a valid JSON object matching this schema:
{{
  "analysis": "2-3 sentences synthesized diagnostic assessment.",
  "observed_facts": ["Concrete fact 1 from telemetry with exact numbers", "Concrete fact 2"],
  "possible_causes": ["Plausible cause 1 explaining the observed facts", "Plausible cause 2"],
  "recommended_actions": ["Specific actionable recommendation 1", "Specific actionable recommendation 2"]
}}
Do NOT include markdown backticks or explanations outside the JSON object.
"""

        prompt = f"User Question: {question}\n\nPlease analyze based on the telemetry context and return the JSON schema."

        response_text = ""
        # Support google.genai Client
        if hasattr(self._gemini_client, "models") and hasattr(self._gemini_client.models, "generate_content"):
            res = self._gemini_client.models.generate_content(
                model=self.model_name,
                contents=[system_prompt, prompt],
            )
            response_text = res.text
        # Support google.generativeai GenerativeModel
        elif hasattr(self._gemini_client, "generate_content"):
            res = self._gemini_client.generate_content(f"{system_prompt}\n\n{prompt}")
            response_text = res.text

        # Parse JSON from response
        clean_json = re.sub(r"^```json\s*", "", response_text.strip(), flags=re.MULTILINE)
        clean_json = re.sub(r"^```\s*$", "", clean_json.strip(), flags=re.MULTILINE).strip()
        data = json.loads(clean_json)
        return data

    def _local_reasoning(self, question: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic, grounded reasoning engine generating factual diagnostics from telemetry."""
        q_lower = question.lower()
        cpu_val = ctx["cpu_utilization_percent"]
        mem_val = ctx["memory_utilization_percent"]
        disk_val = ctx["disk_utilization_percent"]
        risk = ctx["risk_status"]
        top_p = ctx["top_processes"]
        leader_p = top_p[0] if top_p else {"name": "None", "cpu_percent": 0.0, "memory_percent": 0.0, "pid": 0}
        anoms = ctx["active_anomalies"]

        facts = [
            f"Overall CPU utilization is {cpu_val}% across {ctx['logical_cores']} logical threads.",
            f"RAM utilization is {mem_val}% ({ctx['memory_used_gb']} GB used of {ctx['memory_total_gb']} GB).",
            f"Disk volume capacity is at {disk_val}%.",
            f"Leading consumer process is '{leader_p['name']}' (PID {leader_p['pid']}) with {leader_p['cpu_percent']}% CPU and {leader_p['memory_percent']}% RAM.",
        ]

        causes = []
        recs = []
        analysis = ""

        # Query Type: CPU
        if "cpu" in q_lower:
            analysis = (
                f"CPU utilization currently stands at {cpu_val}%, reflecting a '{ctx['cpu_trend']}' trend. "
                f"The highest individual load is generated by '{leader_p['name']}' (PID {leader_p['pid']}) at {leader_p['cpu_percent']}%. "
                f"Short-term forecast: {ctx['cpu_forecast']}."
            )
            if cpu_val >= 75.0:
                causes.append(f"Process '{leader_p['name']}' is executing computational tasks or thread-heavy operations.")
                causes.append("Potential burst activity from system compilers, background indexers, or browser tabs.")
                recs.append(f"Inspect or throttle '{leader_p['name']}' via Process Monitoring.")
                recs.append("Verify CPU cooling and clock throttle limits if high load is sustained.")
            else:
                causes.append("CPU load is within healthy operating boundaries with plenty of headroom.")
                recs.append("No immediate CPU throttling or adjustments required.")

        # Query Type: RAM / Memory
        elif "ram" in q_lower or "memory" in q_lower:
            analysis = (
                f"System physical memory is at {mem_val}% capacity ({ctx['memory_used_gb']} GB allocated). "
                f"Recent memory trajectory is {ctx['memory_trend']}."
            )
            if mem_val >= 80.0:
                causes.append("Active application working sets and OS file buffer caches have accumulated.")
                causes.append("Background memory retention or long-running worker processes consuming RSS.")
                recs.append("Review resident memory sizes in the Process Table and close idle applications.")
                recs.append("Consider increasing physical RAM capacity if load regularly exceeds 85%.")
            else:
                causes.append("Physical RAM is well within stable operating thresholds.")
                recs.append("Memory allocation is balanced; continue monitoring for sudden climbing trends.")

        # Query Type: Top Process / Resource Consumption
        elif "process" in q_lower or "consuming" in q_lower:
            analysis = (
                f"The highest resource footprint is driven by '{leader_p['name']}' (PID {leader_p['pid']}) "
                f"using {leader_p['cpu_percent']}% CPU and {leader_p['memory_percent']}% memory."
            )
            causes.append(f"Process '{leader_p['name']}' is active in foreground or running a background service loop.")
            recs.append(f"Navigate to the Process Monitoring tab to inspect all top {len(top_p)} processes.")

        # Query Type: Anomaly
        elif "anomal" in q_lower:
            if anoms:
                lead_anom = anoms[0]
                analysis = (
                    f"There is currently {len(anoms)} active system anomaly: "
                    f"[{lead_anom['severity']}] on {lead_anom['metric']} (observed {lead_anom['observed_value']}). "
                    f"{lead_anom['explanation']}"
                )
                causes.append("A metric exceeded configured threshold boundaries or deviated from the rolling baseline.")
                recs.append("Review the Anomaly Detection dashboard to check historical occurrence frequency.")
            else:
                analysis = "No active metric anomalies are detected. All system variables remain within baseline distributions."
                causes.append("Telemetry metrics conform to normal distribution models.")
                recs.append("Keep monitoring automated anomaly alerts for proactive warnings.")

        # Query Type: System Health / Risk / General
        else:
            analysis = (
                f"Overall system status is classified as '{risk}' with a composite risk score of {ctx['risk_score']}/100. "
                f"Hardware load: CPU {cpu_val}%, RAM {mem_val}%, Disk {disk_val}%."
            )
            if risk in ["High Risk", "Critical"]:
                causes.append("One or more hardware metrics is near or exceeding safe operational margins.")
                recs.append("Follow highlighted alert recommendations to alleviate system pressure.")
            else:
                causes.append("Telemetry metrics indicate nominal operational performance.")
                recs.append("Maintain routine periodic monitoring.")

        return {
            "analysis": analysis,
            "observed_facts": facts,
            "possible_causes": causes,
            "recommended_actions": recs,
        }

    def generate_system_summary(
        self,
        current_metrics: Any,
        anomalies: List[Any],
        risk_resp: Any,
    ) -> AISummaryResponse:
        """Produce an executive system health statement for the Overview page."""
        now = datetime.now(timezone.utc)
        cpu_val = getattr(current_metrics.cpu, "utilization_percent", 0.0) if current_metrics else 0.0
        mem_val = getattr(current_metrics.memory, "utilization_percent", 0.0) if current_metrics else 0.0
        risk_status = getattr(risk_resp, "risk_status", "Normal") if risk_resp else "Normal"
        anom_count = len(anomalies)

        health_level = "healthy"
        if risk_status == "Critical" or cpu_val >= 90.0 or mem_val >= 92.0:
            health_level = "critical"
            headline = "Critical System Pressure Detected"
            summary = (
                f"The host machine is operating under critical load (CPU {cpu_val}%, RAM {mem_val}%). "
                f"With {anom_count} active anomaly alert(s), immediate resource remediation is advised."
            )
            key_rec = "Identify and throttle high-consumption processes using the Process Table."
        elif risk_status in ["Warning", "High Risk"] or cpu_val >= 75.0 or mem_val >= 80.0 or anom_count > 0:
            health_level = "warning"
            headline = f"System Operating with Elevated Load ({risk_status})"
            summary = (
                f"Moderate resource pressure observed (CPU {cpu_val}%, RAM {mem_val}%). "
                f"{anom_count} anomalous metric event(s) detected. Predictive analytics indicate attention is warranted."
            )
            key_rec = "Review recent anomaly logs and high-memory resident tasks."
        else:
            health_level = "healthy"
            headline = "All System Subsystems Operating Normally"
            summary = (
                f"Host telemetry exhibits stable performance (CPU {cpu_val}%, RAM {mem_val}%). "
                f"Zero critical alerts active and predictive models forecast steady-state continuation."
            )
            key_rec = "System is healthy. No intervention required."

        return AISummaryResponse(
            headline=headline,
            summary=summary,
            health_level=health_level,
            active_concerns_count=anom_count,
            key_recommendation=key_rec,
            source="gemini_api" if self.is_configured() else "grounded_telemetry_engine",
            timestamp=now,
        )


_ai_service_instance: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Retrieve or construct the singleton AIService."""
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance
