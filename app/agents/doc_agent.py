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

branch_doc_writer_agent = Agent(
    name="branch_doc_writer_agent",
    model=get_gemini_model(),
    instruction=(
        "You are the Branch Documentation Writer Agent of K-SCM.\n"
        "Your mission is to draft comprehensive custom branch README.md documentation containing "
        "repository directory tree structures, audit report summaries, and verification checklists."
    ),
    tools=[],
)
