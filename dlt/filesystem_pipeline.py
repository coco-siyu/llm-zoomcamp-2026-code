"""Load local Codex session JSONL logs into DuckDB as raw records."""

import json
from collections.abc import Iterator
from typing import Any

import dlt
from dlt.sources import TDataItems
from dlt.sources.filesystem import FileItemDict, filesystem


PIPELINE_NAME = "codex_sessions_pipeline"
DATASET_NAME = "codex_sessions_data"
TABLE_NAME = "raw_session_events"
FILE_GLOB = "**/*.jsonl"


@dlt.transformer
def read_raw_jsonl(items: Iterator[FileItemDict]) -> Iterator[TDataItems]:
    """Yield one record per JSONL line while preserving the original JSON text."""
    for file_item in items:
        with file_item.open() as file:
            for line_number, raw_line in enumerate(file, start=1):
                if isinstance(raw_line, bytes):
                    raw_line = raw_line.decode("utf-8")

                raw_json = raw_line.rstrip("\r\n")
                if not raw_json.strip():
                    continue

                parsed: dict[str, Any] = json.loads(raw_json)
                yield {
                    "source_path": file_item["relative_path"],
                    "line_number": line_number,
                    "timestamp": parsed.get("timestamp"),
                    "record_type": parsed.get("type"),
                    "raw_json": raw_json,
                }


def load_codex_sessions() -> dlt.Pipeline:
    """Replace the development table with all matching local session records."""
    pipeline = dlt.pipeline(
        pipeline_name=PIPELINE_NAME,
        destination="duckdb",
        dataset_name=DATASET_NAME,
        dev_mode=True,
    )

    session_files = filesystem(file_glob=FILE_GLOB)
    records = (session_files | read_raw_jsonl()).with_name(TABLE_NAME)

    load_info = pipeline.run(records, write_disposition="replace")
    print(load_info)
    print(pipeline.last_trace.last_normalize_info)
    return pipeline


if __name__ == "__main__":
    load_codex_sessions()
