# Analysis Plan: codex_sessions_pipeline

## Connection
pipeline: codex_sessions_pipeline
dataset: codex_sessions_data_20260804081319
destination: duckdb

## Profile Summary
| table | rows | key columns | notes |
|-------|------|-------------|-------|
| raw_session_events | 273 | source_path, line_number, timestamp, record_type, raw_json | 2 source files/sessions; 5 distinct turns; timestamps span 2026-08-04 19:41–20:13 UTC; raw_json is valid JSON |

Record mix: 168 `response_item`, 95 `event_msg`, 5 `turn_context`, 3 `world_state`, and 2 `session_meta` rows. JSON profiling found event and response subtypes, roles, cumulative token counters in 45 `token_count` events, model in 5 turn contexts, and working-directory metadata in session/turn records. `raw_json` may contain user or assistant text, so charts use only aggregate metadata and do not display message content. Working-directory values may reveal local paths.

## Questions
1. [x] When were Codex CLI sessions active? → Chart 1
2. [x] How many records were produced by each record type? → Chart 2
3. [x] Which `event_msg` subtypes occurred most often? → Chart 3
4. [x] Which `response_item` subtypes and roles occurred? → Chart 4
5. [x] How many tokens were reported for each session? → Chart 5
6. [x] Which models were used across turns? → Chart 6
7. [x] Which working directories or projects were used? → Chart 7
8. [x] How many sessions and turns are present? → Chart 8

## Data Gaps
No requested metric is unavailable in the current load. Token values are cumulative snapshots rather than independently additive events; Chart 5 uses the latest snapshot per session. Cached input tokens are a subset of input tokens, and reasoning output tokens are a subset of output tokens, so those series must not be summed together. Project names are not explicit, so Chart 7 labels the available working-directory path as the project proxy.

## Chart 1: Session Activity Over Time
question: When were Codex CLI sessions active?
type: line
x: timestamp (minute)
y: count(records)
source: raw_session_events

```sql
SELECT
    DATE_TRUNC('minute', timestamp) AS activity_minute,
    record_type,
    COUNT(*) AS records
FROM raw_session_events
GROUP BY 1, 2
ORDER BY 1, 2
```

```altair
alt.Chart(df).mark_line(point=True).encode(
    x=alt.X("activity_minute:T", title="Activity minute (UTC)"),
    y=alt.Y("records:Q", title="Records"),
    color=alt.Color("record_type:N", title="Record type"),
    tooltip=["activity_minute:T", "record_type:N", "records:Q"]
).properties(title="Codex CLI activity by minute")
```

## Chart 2: Records by Record Type
question: How many records were produced by each record type?
type: bar
x: count(records)
y: record_type
source: raw_session_events

```sql
SELECT record_type, COUNT(*) AS records
FROM raw_session_events
GROUP BY 1
ORDER BY 2 DESC
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("records:Q", title="Records"),
    y=alt.Y("record_type:N", sort="-x", title="Record type"),
    tooltip=["record_type:N", "records:Q"]
).properties(title="Records by type")
```

## Chart 3: Event Message Subtypes
question: Which event_msg subtypes occurred most often?
type: bar
x: count(records)
y: event_subtype
source: raw_session_events

```sql
SELECT
    COALESCE(json_extract_string(raw_json, '$.payload.type'), '(unavailable)') AS event_subtype,
    COUNT(*) AS records
FROM raw_session_events
WHERE record_type = 'event_msg'
GROUP BY 1
ORDER BY 2 DESC
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("records:Q", title="Event messages"),
    y=alt.Y("event_subtype:N", sort="-x", title="Event subtype"),
    tooltip=["event_subtype:N", "records:Q"]
).properties(title="event_msg subtypes")
```

## Chart 4: Response Item Subtypes and Roles
question: Which response_item subtypes and roles occurred?
type: stacked bar
x: count(records)
y: response_subtype
source: raw_session_events

```sql
SELECT
    COALESCE(json_extract_string(raw_json, '$.payload.type'), '(unavailable)') AS response_subtype,
    COALESCE(json_extract_string(raw_json, '$.payload.role'), '(not applicable)') AS role,
    COUNT(*) AS records
FROM raw_session_events
WHERE record_type = 'response_item'
GROUP BY 1, 2
ORDER BY 1, 2
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("records:Q", title="Response items", stack="zero"),
    y=alt.Y("response_subtype:N", title="Response subtype"),
    color=alt.Color("role:N", title="Role"),
    tooltip=["response_subtype:N", "role:N", "records:Q"]
).properties(title="response_item subtype and role")
```

## Chart 5: Latest Cumulative Token Usage by Session
question: How many tokens were reported for each session?
type: grouped bar
x: session
y: token_count
source: raw_session_events

```sql
WITH token_snapshots AS (
    SELECT
        source_path,
        timestamp,
        TRY_CAST(json_extract_string(raw_json, '$.payload.info.total_token_usage.input_tokens') AS BIGINT) AS input_tokens,
        TRY_CAST(json_extract_string(raw_json, '$.payload.info.total_token_usage.cached_input_tokens') AS BIGINT) AS cached_input_tokens,
        TRY_CAST(json_extract_string(raw_json, '$.payload.info.total_token_usage.output_tokens') AS BIGINT) AS output_tokens,
        TRY_CAST(json_extract_string(raw_json, '$.payload.info.total_token_usage.reasoning_output_tokens') AS BIGINT) AS reasoning_output_tokens,
        TRY_CAST(json_extract_string(raw_json, '$.payload.info.total_token_usage.total_tokens') AS BIGINT) AS total_tokens
    FROM raw_session_events
    WHERE record_type = 'event_msg'
      AND json_extract_string(raw_json, '$.payload.type') = 'token_count'
), latest AS (
    SELECT
        REGEXP_EXTRACT(source_path, '[^/]+$') AS session,
        ARG_MAX(input_tokens, timestamp) AS input_tokens,
        ARG_MAX(cached_input_tokens, timestamp) AS cached_input_tokens,
        ARG_MAX(output_tokens, timestamp) AS output_tokens,
        ARG_MAX(reasoning_output_tokens, timestamp) AS reasoning_output_tokens,
        ARG_MAX(total_tokens, timestamp) AS total_tokens
    FROM token_snapshots
    GROUP BY 1
)
SELECT session, metric, token_count
FROM latest
UNPIVOT (token_count FOR metric IN (total_tokens, input_tokens, cached_input_tokens, output_tokens, reasoning_output_tokens))
ORDER BY session, metric
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("metric:N", title="Cumulative counter"),
    y=alt.Y("token_count:Q", title="Tokens"),
    color=alt.Color("session:N", title="Session file"),
    xOffset="session:N",
    tooltip=["session:N", "metric:N", alt.Tooltip("token_count:Q", format=",")]
).properties(title="Latest cumulative token counters per session")
```

## Chart 6: Model Usage by Turn
question: Which models were used across turns?
type: bar
x: model
y: distinct turns
source: raw_session_events

```sql
SELECT
    COALESCE(json_extract_string(raw_json, '$.payload.model'), '(unavailable)') AS model,
    COUNT(DISTINCT json_extract_string(raw_json, '$.payload.turn_id')) AS turns
FROM raw_session_events
WHERE record_type = 'turn_context'
GROUP BY 1
ORDER BY 2 DESC
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("model:N", title="Model"),
    y=alt.Y("turns:Q", title="Distinct turns"),
    tooltip=["model:N", "turns:Q"]
).properties(title="Model usage by turn")
```

## Chart 7: Working Directories and Projects
question: Which working directories or projects were used?
type: bar
x: distinct turns
y: working_directory
source: raw_session_events

```sql
SELECT
    COALESCE(json_extract_string(raw_json, '$.payload.cwd'), '(unavailable)') AS working_directory,
    COUNT(DISTINCT json_extract_string(raw_json, '$.payload.turn_id')) AS turns
FROM raw_session_events
WHERE record_type = 'turn_context'
GROUP BY 1
ORDER BY 2 DESC
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("turns:Q", title="Distinct turns"),
    y=alt.Y("working_directory:N", sort="-x", title="Working directory (project proxy)"),
    tooltip=["working_directory:N", "turns:Q"]
).properties(title="Turns by working directory")
```

## Chart 8: Sessions and Turns
question: How many sessions and turns are present?
type: bar
x: metric
y: count
source: raw_session_events

```sql
SELECT 'Sessions' AS metric,
       COUNT(DISTINCT json_extract_string(raw_json, '$.payload.id')) AS count
FROM raw_session_events
WHERE record_type = 'session_meta'
UNION ALL
SELECT 'Turns' AS metric,
       COUNT(DISTINCT json_extract_string(raw_json, '$.payload.turn_id')) AS count
FROM raw_session_events
WHERE record_type = 'turn_context'
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("metric:N", title=None),
    y=alt.Y("count:Q", title="Count"),
    color=alt.Color("metric:N", legend=None),
    tooltip=["metric:N", "count:Q"]
).properties(title="Available session and turn counts")
```
