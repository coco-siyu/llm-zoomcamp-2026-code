from typing import Any

import dlt
from dlt.sources.rest_api import RESTAPIConfig, rest_api_resources


API_BASE_URL = "https://test-agent-traces-api-xt2e7ottma-ew.a.run.app/"


@dlt.source(name="agent_traces")
def agent_traces_source(page_size: int = 1_000) -> Any:
    """Load Claude Code-style agent logs from the public traces API.

    Args:
        page_size: Number of logs requested per API call (maximum 1,000).
    """
    config: RESTAPIConfig = {
        "client": {
            "base_url": API_BASE_URL,
            "paginator": {
                "type": "offset",
                "limit": page_size,
                "offset": 0,
                "offset_param": "offset",
                "limit_param": "limit",
                "total_path": "total",
                "maximum_offset": 20_000,
            },
        },
        "resources": [
            {
                "name": "logs",
                "primary_key": "index",
                "write_disposition": "replace",
                "endpoint": {
                    "path": "logs",
                    "data_selector": "logs",
                },
            }
        ],
    }

    yield from rest_api_resources(config)


def load_agent_traces() -> None:
    """Replace the DuckDB table with exactly the first 20,000 API logs."""
    pipeline = dlt.pipeline(
        pipeline_name="agent_traces_pipeline",
        destination="playground",
        dataset_name="agent_traces_data",
    )

    # The paginator is bounded at offset 20,000; the page cap is a second guard.
    load_info = pipeline.run(agent_traces_source().add_limit(20))
    print(load_info)  # noqa: T201


if __name__ == "__main__":
    load_agent_traces()
