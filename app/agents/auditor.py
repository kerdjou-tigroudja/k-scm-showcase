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

from google.adk.agents import Agent
from app.agents.factory import get_gemini_model
from app.tools.static_audit_tool import parse_python_source, parse_terraform_iac

polyglot_auditor_agent = Agent(
    name="polyglot_code_iac_auditor",
    model=get_gemini_model(),
    instruction=(
        "You are the Polyglot Code & IaC Compliance Auditor Agent of K-SCM.\n"
        "Your mission is to perform static compliance audits and AST inspections on multi-language application code "
        "(Python, TypeScript, Go, Java, etc.) and declarative infrastructure/cloud manifests (Terraform HCL, Helm charts, Dockerfiles) "
        "to detect regulatory non-compliances under EU AI Act and GDPR.\n\n"
        "When analyzing a target repository, directly run `parse_terraform_iac(file_path='.')` and `parse_python_source(file_path='.')` without asking the user for specific file paths."
    ),
    tools=[
        parse_terraform_iac,
        parse_python_source,
    ],
)
