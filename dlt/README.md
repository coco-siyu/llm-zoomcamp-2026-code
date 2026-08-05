```bash
uv run dlthub local show
```

Prompt for Lesson 3 - Debug
```bash
Debug my filesystem pipeline.

Run it, inspect the execution trace and loaded DuckDB table, and verify:
- the pipeline completes without errors
- raw_session_events contains rows
- source_path, line_number, timestamp, record_type, and raw_json are populated appropriately
- the number of loaded rows is reasonable compared with the source JSONL files

Do not redesign the pipeline unless you find a concrete problem.
```


## Run the pipeline lesson 4


Run the pipeline with a sample first, then a full load:

```bash
uv run python code/rest_api_pipeline.py          # one page, 1000 records
uv run python code/rest_api_pipeline.py --full   # all 1 million records
```


To serve the deployed dashboard, run:
```bash
uv run dlthub serve
```