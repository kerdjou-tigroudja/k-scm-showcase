# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from typing import Any

from dotenv import load_dotenv
from google.adk.models import Gemini
from google.genai import types

load_dotenv()


def _get_clean_env_location(key: str) -> str | None:
    val = os.environ.get(key)
    if val:
        return val.strip('"\' ')
    return None


def get_model_policy() -> str:
    """Returns the requested model policy from environment configuration."""
    endpoint_id = os.environ.get("AGENT_PLATFORM_ENDPOINT_ID") or os.environ.get("GEMINI_ENDPOINT")
    if endpoint_id:
        if endpoint_id.startswith("projects/"):
            return endpoint_id
        project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID") or ""
        location = os.environ.get("GOOGLE_CLOUD_LOCATION") or os.environ.get("LOCATION") or "europe-west9"
        return f"projects/{project}/locations/{location}/endpoints/{endpoint_id}"
    return os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")


def get_gemini_model(model_name: str | None = None) -> Gemini:
    """
    Returns a configured ADK Gemini model.
    For raw publisher models under Vertex AI Direct API, routes location to global/eu
    (GEMINI_LOCATION / GEMINI_PREVIEW_LOCATION) to prevent 404 NOT_FOUND errors, while
    preserving europe-west9 for Agent Platform hosted endpoints and sovereign data storage.
    """
    model = model_name or get_model_policy()
    client_kwargs: dict[str, Any] = {}

    if not model.startswith("projects/"):
        use_enterprise = os.environ.get("GOOGLE_GENAI_USE_ENTERPRISE", "").lower() in ("true", "1")
        if use_enterprise:
            location = _get_clean_env_location("GEMINI_LOCATION") or _get_clean_env_location("GEMINI_PREVIEW_LOCATION") or "global"
            client_kwargs["location"] = location

    return Gemini(
        model=model,
        client_kwargs=client_kwargs if client_kwargs else None,
        retry_options=types.HttpRetryOptions(attempts=3),
    )


def resolve_model_config() -> dict[str, Any]:
    """
    Resolves the model configuration, distinguishing model_policy from resolved_model_id.
    """
    policy = get_model_policy()
    use_enterprise = os.environ.get("GOOGLE_GENAI_USE_ENTERPRISE", "").lower() in ("true", "1")
    if not policy.startswith("projects/") and use_enterprise:
        region = _get_clean_env_location("GEMINI_LOCATION") or _get_clean_env_location("GEMINI_PREVIEW_LOCATION") or "global"
    else:
        region = _get_clean_env_location("GOOGLE_CLOUD_LOCATION") or "europe-west9"

    resolved_id = os.environ.get("RESOLVED_GEMINI_MODEL", policy)
    preferred = os.environ.get("GEMINI_MODEL_PREFERRED")

    api_provider = "Vertex AI Direct API" if use_enterprise else "Google GenAI API"
    if policy.startswith("projects/"):
        api_provider = "Agent Platform Hosted Model Endpoint"
        region = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west9")

    return {
        "model_policy": policy,
        "resolved_model_id": resolved_id,
        "api_provider": api_provider,
        "region": region,
        "fallback_active": bool(preferred and policy != preferred),
    }
