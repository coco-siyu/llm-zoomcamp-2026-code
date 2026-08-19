from datetime import UTC, datetime, timedelta
from typing import Any, Iterator

import dlt
from logfire.query_client import LogfireQueryClient
from dotenv import load_dotenv


load_dotenv()


@dlt.source(name="logfire")
def logfire_source(
    page_size: int = 1_000,
) -> Any:
    """Read trace records incrementally from the Pydantic Logfire Query API.

    Args:
        page_size: Records requested per API call; Logfire allows at most 10,000.

    The read token is resolved by dlt from the LOGFIRE_READ_TOKEN environment
    variable and is never logged or persisted by this pipeline.
    """
    if not 1 <= page_size <= 10_000:
        raise ValueError("page_size must be between 1 and 10,000")

    read_token = dlt.secrets["logfire_read_token"]
    initial_timestamp = (datetime.now(tz=UTC) - timedelta(days=365)).isoformat()

    @dlt.resource(
        name="traces",
        primary_key=("trace_id", "span_id"),
        write_disposition="merge",
    )
    def traces(
        start_timestamp: dlt.sources.incremental[str] = dlt.sources.incremental(
            "start_timestamp",
            initial_value=initial_timestamp,
            primary_key=("trace_id", "span_id"),
            row_order="asc",
            lag=300,
        ),
    ) -> Iterator[list[dict[str, Any]]]:
        min_timestamp = datetime.fromisoformat(
            str(start_timestamp.start_value).replace("Z", "+00:00")
        )
        page_cursor: tuple[str, str, str] | None = None

        with LogfireQueryClient(read_token=read_token) as client:
            while True:
                cursor_filter = ""
                if page_cursor is not None:
                    cursor_timestamp, cursor_trace_id, cursor_span_id = page_cursor
                    cursor_filter = f"""
                        WHERE start_timestamp > '{cursor_timestamp}'
                           OR (start_timestamp = '{cursor_timestamp}'
                               AND trace_id > '{cursor_trace_id}')
                           OR (start_timestamp = '{cursor_timestamp}'
                               AND trace_id = '{cursor_trace_id}'
                               AND span_id > '{cursor_span_id}')
                    """

                sql = f"""
                    SELECT *
                    FROM records
                    {cursor_filter}
                    ORDER BY start_timestamp, trace_id, span_id
                    LIMIT {page_size:d}
                """
                response = client.query_json_rows(
                    sql=sql,
                    min_timestamp=min_timestamp,
                    limit=page_size,
                )
                rows = response["rows"]
                if not rows:
                    break

                yield rows
                if len(rows) < page_size:
                    break

                last_row = rows[-1]
                next_cursor = (
                    last_row["start_timestamp"],
                    last_row["trace_id"],
                    last_row["span_id"],
                )
                if next_cursor == page_cursor:
                    raise RuntimeError("Logfire pagination cursor did not advance")
                page_cursor = next_cursor

    return traces


def load_logfire() -> None:
    """Load Logfire records into local DuckDB."""
    pipeline = dlt.pipeline(
        pipeline_name="logfire_agent_traces",
        destination="duckdb",
        dataset_name="agent_traces",
    )

    load_info = pipeline.run(logfire_source())
    print(load_info)  # noqa: T201


if __name__ == "__main__":
    load_logfire()
