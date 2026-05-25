"""
Arize Phoenix observability bootstrap for PetDigiTwin.
Uses OpenTelemetry + OpenInference instrumentors when available.
"""

import os
from urllib.parse import urlparse
from typing import Any, Dict, List
from dotenv import load_dotenv

load_dotenv()


_STATE: Dict[str, Any] = {
    "initialized": False,
    "enabled": False,
    "service_name": None,
    "endpoint": None,
    "instrumentors": [],
    "errors": [],
}


def _otlp_traces_endpoint(raw_endpoint: str) -> str:
    endpoint = raw_endpoint.rstrip("/")
    if endpoint.endswith("/v1/traces"):
        return endpoint
    # Preserve any path segments (including /s/<space>) for Phoenix Cloud spaces.
    return f"{endpoint}/v1/traces"


def setup_observability() -> Dict[str, Any]:
    """Initialize tracing once. Safe to call repeatedly."""
    if _STATE["initialized"]:
        return get_observability_status()

    _STATE["initialized"] = True

    enabled = os.getenv("ENABLE_ARIZE_TRACING", "true").lower() == "true"
    api_key = os.getenv("PHOENIX_API_KEY", "").strip()
    collector = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "").strip()
    service_name = os.getenv("OTEL_SERVICE_NAME", "petdigitwin-agent")

    _STATE["service_name"] = service_name

    if not enabled:
        _STATE["errors"].append("Tracing disabled by ENABLE_ARIZE_TRACING=false")
        return get_observability_status()

    if not api_key or not collector:
        _STATE["errors"].append(
            "Missing PHOENIX_API_KEY or PHOENIX_COLLECTOR_ENDPOINT; tracing not started"
        )
        return get_observability_status()

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        endpoint = _otlp_traces_endpoint(collector)
        headers = {
            "authorization": f"Bearer {api_key}",
        }

        provider = TracerProvider(
            resource=Resource.create(
                {
                    "service.name": service_name,
                    "deployment.environment": os.getenv("ENVIRONMENT", "local"),
                }
            )
        )
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, headers=headers))
        )
        trace.set_tracer_provider(provider)

        _STATE["enabled"] = True
        _STATE["endpoint"] = endpoint
    except Exception as exc:
        _STATE["errors"].append(f"OTLP setup failed: {exc}")
        return get_observability_status()

    # Try OpenInference instrumentors without hard-failing the app.
    try:
        from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor

        GoogleGenAIInstrumentor().instrument()
        _STATE["instrumentors"].append("google-genai")
    except Exception as exc:
        _STATE["errors"].append(f"google-genai instrumentor unavailable: {exc}")

    try:
        from openinference.instrumentation.vertexai import VertexAIInstrumentor

        VertexAIInstrumentor().instrument()
        _STATE["instrumentors"].append("vertexai")
    except Exception as exc:
        _STATE["errors"].append(f"vertexai instrumentor unavailable: {exc}")

    return get_observability_status()


def get_observability_status() -> Dict[str, Any]:
    """Return a safe status object for APIs and health checks."""
    return {
        "initialized": _STATE["initialized"],
        "enabled": _STATE["enabled"],
        "service_name": _STATE["service_name"],
        "endpoint": _STATE["endpoint"],
        "instrumentors": list(_STATE["instrumentors"]),
        "errors": list(_STATE["errors"]),
    }
