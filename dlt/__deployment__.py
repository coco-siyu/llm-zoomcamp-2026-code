"""Lesson 5 — ingest agent traces and explore them in Marimo."""

from dlt.hub import run

import agent_traces_pipeline_dashboard
from rest_api_pipeline import load_agent_traces as _load_agent_traces


@run.pipeline("agent_traces_pipeline", section="rest_api_pipeline")
def run_agent_traces_pipeline() -> None:
    """Load the bounded agent-traces dataset as a batch job."""
    _load_agent_traces()


__all__ = ["run_agent_traces_pipeline", "agent_traces_pipeline_dashboard"]
