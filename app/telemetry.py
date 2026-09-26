"""OpenTelemetry and Cloud Trace setup for K-SCM."""

import logging
import os

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

logger = logging.getLogger(__name__)

# Global telemetry state
_tracer_provider: TracerProvider | None = None
_in_memory_exporter: InMemorySpanExporter | None = None


def setup_telemetry(service_name: str = "k-scm") -> TracerProvider:
    """Initializes OpenTelemetry TracerProvider with Cloud Trace exporter or fallback exporter."""
    global _tracer_provider, _in_memory_exporter

    if _tracer_provider is not None:
        return _tracer_provider

    provider = TracerProvider()
    exporter_type = "in_memory"

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")

    if project_id:
        try:
            from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

            cloud_exporter = CloudTraceSpanExporter(project_id=project_id)
            provider.add_span_processor(SimpleSpanProcessor(cloud_exporter))
            exporter_type = "gcp_cloud_trace"
            logger.info(f"OpenTelemetry configured with GCP Cloud Trace (Project: {project_id})")
        except Exception as e:
            logger.warning(f"Could not initialize GCP Cloud Trace exporter: {e}. Falling back to InMemorySpanExporter.")
            _in_memory_exporter = InMemorySpanExporter()
            provider.add_span_processor(SimpleSpanProcessor(_in_memory_exporter))
    else:
        _in_memory_exporter = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(_in_memory_exporter))

    trace.set_tracer_provider(provider)
    _tracer_provider = provider
    logger.info(f"Telemetry initialized for service '{service_name}' using exporter '{exporter_type}'.")
    return provider
