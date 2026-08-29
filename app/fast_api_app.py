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

import contextlib
import os
from collections.abc import AsyncIterator

import google.auth
from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner
from google.cloud import logging as google_cloud_logging

import uuid
from typing import Literal
from pydantic import BaseModel, Field

from app.app_utils import services
from app.app_utils.a2a import attach_a2a_routes
from app.telemetry import setup_telemetry


class Feedback(BaseModel):
    """Represents feedback for a conversation."""

    score: int | float
    text: str | None = ""
    log_type: Literal["feedback"] = "feedback"
    service_name: Literal["k-scm"] = "k-scm"
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


load_dotenv()
setup_telemetry("k-scm")
_, project_id = google.auth.default()
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from app.agent import app as adk_app
    from app.agent import root_agent

    runner = Runner(
        app=adk_app,
        session_service=services.get_session_service(),
        artifact_service=services.get_artifact_service(),
        auto_create_session=True,
    )
    app.state.runner = runner
    app.state.agent_app_name = adk_app.name
    await attach_a2a_routes(
        app,
        agent=root_agent,
        runner=runner,
        task_store=InMemoryTaskStore(),
        rpc_path=f"/a2a/{adk_app.name}",
    )
    yield


from fastapi.responses import RedirectResponse, Response

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=services.ARTIFACT_SERVICE_URI,
    allow_origins=allow_origins,
    session_service_uri=services.SESSION_SERVICE_URI,
    otel_to_cloud=True,
    lifespan=lifespan,
)
app.title = "k-scm"
app.description = "API for interacting with the Agent k-scm"
app.description = "API for interacting with the Agent k-scm"

# PRISM_DARK_CSS theme definition for dev-ui code highlighting
PRISM_DARK_CSS = """/* PrismJS Dark Theme for ADK Dev-UI Code Highlighting */
code[class*="language-"], pre[class*="language-"] {
    color: #f8f8f2; background: none; font-family: monospace; font-size: 1em; line-height: 1.5;
}
pre[class*="language-"] { padding: 1em; margin: .5em 0; overflow: auto; background: #1e1e1e; }
:not(pre) > code[class*="language-"], pre[class*="language-"] { background: #1e1e1e; }
.token.comment, .token.prolog { color: #6272a4; }
.token.punctuation { color: #f8f8f2; }
.token.property, .token.tag, .token.constant { color: #ff79c6; }
.token.boolean, .token.number { color: #bd93f9; }
.token.selector, .token.attr-name, .token.string { color: #50fa7b; }
.token.operator, .token.entity, .token.url { color: #f8f8f2; }
.token.atrule, .token.attr-value, .token.function, .token.class-name { color: #f1fa8c; }
.token.keyword { color: #8be9fd; }
.token.regex, .token.important { color: #ffb86c; }
"""





@app.get("/dev-ui/prism-dark.css", include_in_schema=False)
async def serve_prism_dark_css() -> Response:
    """Serves the Prism Dark CSS theme to prevent 404s on ADK Dev-UI."""
    return Response(content=PRISM_DARK_CSS, media_type="text/css")


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

