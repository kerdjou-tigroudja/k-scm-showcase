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

"""
Unit tests for model location routing in audit_orchestrator under KER-150.
Validates KER-150 requirement that gemini-3.5-flash routes client location to europe-west9
under Vertex AI Enterprise mode, while gemini-3.6-flash preview routes to global.
"""

import os
from app.agents.factory import get_gemini_model, resolve_model_config
from app.agents.orchestrator import orchestrator_agent


def test_gemini_35_flash_location_routing(monkeypatch):
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "true")
    monkeypatch.setenv("GEMINI_LOCATION", "europe-west9")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.5-flash")

    model = get_gemini_model()
    assert model.model == "gemini-3.5-flash"
    assert model.client_kwargs == {"location": "europe-west9"}


def test_gemini_35_flash_eu_location_routing(monkeypatch):
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "true")
    monkeypatch.setenv("GEMINI_LOCATION", "eu")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.5-flash")

    model = get_gemini_model()
    assert model.model == "gemini-3.5-flash"
    assert model.client_kwargs == {"location": "eu"}

    config = resolve_model_config()
    assert config["region"] == "eu"
    assert config["api_provider"] == "Vertex AI Direct API"


def test_gemini_35_flash_global_default(monkeypatch):
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "true")
    monkeypatch.delenv("GEMINI_LOCATION", raising=False)
    monkeypatch.delenv("GEMINI_PREVIEW_LOCATION", raising=False)
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.5-flash")

    model = get_gemini_model()
    assert model.model == "gemini-3.5-flash"
    assert model.client_kwargs == {"location": "global"}


def test_audit_orchestrator_model_configuration(monkeypatch):
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "true")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    assert orchestrator_agent.name == "audit_orchestrator"
    assert orchestrator_agent.model.model == "gemini-3.5-flash"


def test_resolve_model_config_decoupling(monkeypatch):
    monkeypatch.setenv("GOOGLE_GENAI_USE_ENTERPRISE", "true")
    monkeypatch.setenv("GEMINI_LOCATION", "europe-west9")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.5-flash")

    config = resolve_model_config()
    assert config["model_policy"] == "gemini-3.5-flash"
    assert config["api_provider"] == "Vertex AI Direct API"
    assert config["region"] == "europe-west9"

