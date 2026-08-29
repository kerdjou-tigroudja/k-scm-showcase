"""OpenTelemetry, Cloud Trace, and LLM Latency Telemetry for K-SCM."""

import functools
import logging
import math
import os
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.telemetry_redactor import redact_attributes

logger = logging.getLogger(__name__)

# Global telemetry state
_tracer_provider: TracerProvider | None = None
_in_memory_exporter: InMemorySpanExporter | None = None


class LLMMetricsTracker:
    """Thread-safe collector for tracking LLM execution durations and computing p95 latencies."""

    def __init__(self, max_samples: int = 1000) -> None:
        self.max_samples = max_samples
        self.latencies_ms: list[float] = []
        self.total_tokens: int = 0
        self.total_calls: int = 0
        self.error_count: int = 0
        self.active_spans: int = 0

    def record_llm_call(
        self, duration_ms: float, tokens: int = 0, success: bool = True
    ) -> None:
        """Records an LLM call duration in milliseconds and token counts."""
        self.total_calls += 1
        if not success:
            self.error_count += 1

        self.total_tokens += tokens
        self.latencies_ms.append(duration_ms)

        # Retain last N samples for percentile calculations
        if len(self.latencies_ms) > self.max_samples:
            self.latencies_ms.pop(0)

    def _compute_percentile(self, percentile: float) -> float:
        """Computes given percentile (0 to 100) from latency samples."""
        if not self.latencies_ms:
            return 0.0

        sorted_samples = sorted(self.latencies_ms)
        n = len(sorted_samples)
        if n == 1:
            return round(sorted_samples[0], 2)

        # Percentile rank calculation
        k = (n - 1) * (percentile / 100.0)
        f = math.floor(k)
        c = math.ceil(k)

        if f == c:
            return round(sorted_samples[int(k)], 2)

        d0 = sorted_samples[int(f)] * (c - k)
        d1 = sorted_samples[int(c)] * (k - f)
        return round(d0 + d1, 2)

    def get_p50_latency(self) -> float:
        """Returns median p50 latency in ms."""
        return self._compute_percentile(50.0)

    def get_p90_latency(self) -> float:
        """Returns 90th percentile p90 latency in ms."""
        return self._compute_percentile(90.0)

    def get_p95_latency(self) -> float:
        """Returns 95th percentile p95 latency in ms."""
        return self._compute_percentile(95.0)

    def get_p99_latency(self) -> float:
        """Returns 99th percentile p99 latency in ms."""
        return self._compute_percentile(99.0)

    def get_summary(self) -> dict[str, Any]:
        """Returns structured summary of telemetry metrics."""
        avg_latency = (
            round(sum(self.latencies_ms) / len(self.latencies_ms), 2)
            if self.latencies_ms
            else 0.0
        )
        error_rate = (
            round((self.error_count / self.total_calls) * 100, 2)
            if self.total_calls > 0
            else 0.0
        )

        return {
            "total_llm_calls": self.total_calls,
            "total_tokens_consumed": self.total_tokens,
            "error_count": self.error_count,
            "error_rate_pct": error_rate,
            "avg_latency_ms": avg_latency,
            "p50_latency_ms": self.get_p50_latency(),
            "p90_latency_ms": self.get_p90_latency(),
            "p95_latency_ms": self.get_p95_latency(),
            "p99_latency_ms": self.get_p99_latency(),
            "sample_count": len(self.latencies_ms),
            "cloud_trace_region": os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west9"),
            "cloud_trace_active": _tracer_provider is not None,
        }


# Global metrics instance
llm_metrics = LLMMetricsTracker()


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


def get_tracer(name: str = "k-scm") -> trace.Tracer:
    """Returns an OpenTelemetry tracer."""
    return trace.get_tracer(name)


@contextmanager
def telemetry_span(span_name: str, attributes: dict[str, Any] | None = None) -> Generator[trace.Span, None, None]:
    """Context manager to execute a code block within an OpenTelemetry span with sanitized attributes."""
    tracer = get_tracer()
    llm_metrics.active_spans += 1
    sanitized_attrs = redact_attributes(attributes)
    with tracer.start_as_current_span(span_name) as span:
        for k, v in sanitized_attrs.items():
            span.set_attribute(k, v)
        try:
            yield span
        finally:
            llm_metrics.active_spans = max(0, llm_metrics.active_spans - 1)


def measure_llm_latency(span_name: str = "llm_inference") -> Callable:
    """Decorator measuring execution duration of an LLM call and logging it to telemetry metrics."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            success = True
            try:
                with telemetry_span(span_name):
                    result = func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                llm_metrics.record_llm_call(duration_ms=duration_ms, success=success)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            success = True
            try:
                with telemetry_span(span_name):
                    result = await func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                llm_metrics.record_llm_call(duration_ms=duration_ms, success=success)

        if asyncio_is_coroutine_function(func):
            return async_wrapper
        return wrapper

    return decorator


def asyncio_is_coroutine_function(func: Any) -> bool:
    import asyncio
    return asyncio.iscoroutinefunction(func)


def get_telemetry_metrics() -> dict[str, Any]:
    """Returns current OpenTelemetry and LLM latency p95 metrics summary."""
    return llm_metrics.get_summary()
