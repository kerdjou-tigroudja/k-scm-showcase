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

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from app.agents.adr_agent import adr_architect_agent
from app.agents.auditor import polyglot_auditor_agent
from app.agents.doc_agent import branch_doc_writer_agent
from app.agents.gitops_agent import gitops_remediation_agent
from app.agents.rag_agent import regulatory_rag_agent
from app.tools import (
    generate_madr_adr,
    parse_python_source,
    parse_terraform_iac,
    query_regulatory_rag,
    submit_hitl_remediation_review,
)


from app.agents.factory import get_gemini_model, get_model_policy, resolve_model_config

MODEL = get_model_policy()

SYSTEM_INSTRUCTION = (
    "You are K-SCM (Sovereign Compliance Mesh) Autonomous Compliance Supervisor Agent.\n"
    "Your mission is to orchestrate a multi-agent team performing static compliance audits and remediations on Terraform IaC (.tf), "
    "cloud manifests, and multi-language application code (Python, TypeScript, Go, Java) "
    "under EU AI Act and GDPR regulations in GCP sovereign region europe-west9 (Paris, SecNumCloud).\n\n"
    "STRICT DELEGATION RULE: As the supervisor agent, you MUST NOT execute tool calls directly. "
    "You MUST DELEGATE all static inspection, regulatory RAG queries, ADR generation, and GitOps remediations exclusively "
    "to your specialized sub-agents.\n\n"
    "You supervise 5 specialized sub-agents:\n"
    "1. `polyglot_code_iac_auditor`: Delegate static inspection of IaC and source code AST to this agent.\n"
    "2. `regulatory_rag_agent`: Delegate grounding findings against EU AI Act / GDPR legal articles to this agent.\n"
    "3. `adr_architect_agent`: Delegate generation of MADR v3 English ADRs and unified patch diffs to this agent.\n"
    "4. `branch_doc_writer_agent`: Delegate formatting custom branch README.md documentation to this agent.\n"
    "5. `gitops_remediation_agent`: Delegate applying patches, committing, pushing, and opening GitHub Draft PRs to this agent.\n\n"
    "Follow this strict 5-step compliance workflow by delegating to your sub-agents:\n"
    "1. STATIC AUDIT: Delegate to `polyglot_code_iac_auditor` to detect violations in IaC and application code.\n"
    "2. REGULATORY GROUNDING: Delegate to `regulatory_rag_agent` to retrieve official EU AI Act / GDPR legal articles.\n"
    "3. ADR MADR GENERATION: Delegate to `adr_architect_agent` to format English MADR v3 Architecture Decision Records.\n"
    "4. HUMAN-IN-THE-LOOP GITOPS SUBMISSION: Delegate to `gitops_remediation_agent` to apply patch diffs, write branch README.md, commit, push to GitHub, and create a Draft PR.\n"
    "5. FINAL EXECUTIVE REPORT: MANDATORY - Once all sub-agents complete their tasks, output a comprehensive Markdown Executive Compliance Report summarizing:\n"
    "   - Executive Audit Overview & Scope\n"
    "   - Table of Detected Violations (File, Severity, Rule, Framework)\n"
    "   - Regulatory Citations & Legal Justification (EU AI Act & GDPR)\n"
    "   - Summary of MADR Architecture Decision Records\n"
    "   - GitOps PR Submission Links & Next Steps for Human Approval."
)

orchestrator_agent = Agent(
    name="audit_orchestrator",
    model=get_gemini_model(),
    instruction=SYSTEM_INSTRUCTION,
    sub_agents=[
        polyglot_auditor_agent,
        regulatory_rag_agent,
        adr_architect_agent,
        branch_doc_writer_agent,
        gitops_remediation_agent,
    ],
)
