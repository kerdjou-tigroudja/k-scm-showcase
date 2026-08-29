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
from app.tools.rag_tool import query_regulatory_rag

regulatory_rag_agent = Agent(
    name="regulatory_rag_agent",
    model=get_gemini_model(),
    instruction=(
        "You are the Regulatory RAG Grounding Agent of K-SCM.\n"
        "Your mission is to query AlloyDB pgvector or local regulatory vector stores to retrieve official legal articles "
        "and recitals from EU AI Act and GDPR matching detected non-compliances."
    ),
    tools=[
        query_regulatory_rag,
    ],
)
