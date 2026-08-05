# Analysis Plan: agent_traces_pipeline

## Connection
pipeline: agent_traces_pipeline
dataset: agent_traces_data
destination: duckdb

## Profile Summary
| table | rows | key columns | notes |
|-------|------|-------------|-------|
| logs | 20,000 | index, timestamp, session_id, type, cwd, git_branch, message__model, usage__input_tokens, usage__output_tokens | 2,476 sessions; 5 projects; 4 models; timestamps span 2026-01-01 00:00 through 2026-01-02 14:53 UTC |
| logs__message__content | 19,668 | type, text, name, input__description, _dlt_parent_id | Normalized content blocks: 13,024 text and 6,644 tool-use rows |

Aggregate token totals are 330,089,822 input tokens and 26,215,151 output tokens. Message text, tool inputs, UUIDs, session IDs, and full local paths can contain sensitive operational context, so the report displays only aggregate metadata and short project labels derived from `cwd`.

## Questions
1. [x] When was agent activity highest? → Chart 1
2. [x] How did input and output token usage change over time? → Chart 2
3. [x] How does token usage compare across models? → Chart 3
4. [x] What is the user-versus-assistant message mix? → Chart 4
5. [x] Which tools were used most often? → Chart 5
6. [x] Which projects generated the most sessions and logs? → Chart 6
7. [x] How was activity distributed across Git branches? → Chart 7
8. [x] What is the distribution of session sizes? → Chart 8

## Data Gaps
No explicit monetary cost or per-model pricing fields are available, so the dashboard reports tokens rather than estimated spend. The API exposes synthetic Claude-style logs, so Codex-specific cached/reasoning token counters are unavailable. Project names are derived from the final segment of `cwd`.

## Chart 1: Agent Activity Over Time
question: When was agent activity highest?
type: line
x: timestamp (hourly)
y: count(logs)
source: logs

```sql
SELECT
    DATE_TRUNC('hour', timestamp) AS activity_hour,
    type,
    COUNT(*) AS logs
FROM logs
GROUP BY 1, 2
ORDER BY 1, 2
```

```altair
alt.Chart(df).mark_area(opacity=0.72).encode(
    x=alt.X("activity_hour:T", title="Hour (UTC)"),
    y=alt.Y("logs:Q", title="Log records", stack="zero"),
    color=alt.Color("type:N", title="Message type"),
    tooltip=["activity_hour:T", "type:N", alt.Tooltip("logs:Q", format=",")]
).properties(title="Agent activity by hour")
```

## Chart 2: Token Usage Over Time
question: How did input and output token usage change over time?
type: line
x: timestamp (hourly)
y: sum(tokens)
source: logs

```sql
WITH hourly AS (
    SELECT
        DATE_TRUNC('hour', timestamp) AS activity_hour,
        SUM(COALESCE(usage__input_tokens, 0)) AS input_tokens,
        SUM(COALESCE(usage__output_tokens, 0)) AS output_tokens
    FROM logs
    GROUP BY 1
)
SELECT activity_hour, token_type, tokens
FROM hourly
UNPIVOT (tokens FOR token_type IN (input_tokens, output_tokens))
ORDER BY activity_hour, token_type
```

```altair
alt.Chart(df).mark_line(point=True).encode(
    x=alt.X("activity_hour:T", title="Hour (UTC)"),
    y=alt.Y("tokens:Q", title="Tokens"),
    color=alt.Color("token_type:N", title="Token type"),
    tooltip=["activity_hour:T", "token_type:N", alt.Tooltip("tokens:Q", format=",")]
).properties(title="Hourly token usage")
```

## Chart 3: Token Usage by Model
question: How does token usage compare across models?
type: stacked bar
x: model
y: sum(tokens)
source: logs

```sql
WITH model_tokens AS (
    SELECT
        message__model AS model,
        SUM(COALESCE(usage__input_tokens, 0)) AS input_tokens,
        SUM(COALESCE(usage__output_tokens, 0)) AS output_tokens
    FROM logs
    WHERE message__model IS NOT NULL
    GROUP BY 1
)
SELECT model, token_type, tokens
FROM model_tokens
UNPIVOT (tokens FOR token_type IN (input_tokens, output_tokens))
ORDER BY model, token_type
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("model:N", title="Model", sort="-y"),
    y=alt.Y("tokens:Q", title="Tokens", stack="zero"),
    color=alt.Color("token_type:N", title="Token type"),
    tooltip=["model:N", "token_type:N", alt.Tooltip("tokens:Q", format=",")]
).properties(title="Token usage by model")
```

## Chart 4: Message Mix
question: What is the user-versus-assistant message mix?
type: bar
x: type
y: count(logs)
source: logs

```sql
SELECT type, COUNT(*) AS logs
FROM logs
GROUP BY 1
ORDER BY 2 DESC
```

```altair
alt.Chart(df).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
    x=alt.X("type:N", title="Message type"),
    y=alt.Y("logs:Q", title="Log records"),
    color=alt.Color("type:N", legend=None),
    tooltip=["type:N", alt.Tooltip("logs:Q", format=",")]
).properties(title="User and assistant messages")
```

## Chart 5: Most-Used Tools
question: Which tools were used most often?
type: bar
x: count(tool calls)
y: tool name
source: logs__message__content

```sql
SELECT name AS tool_name, COUNT(*) AS tool_calls
FROM logs__message__content
WHERE type = 'tool_use' AND name IS NOT NULL
GROUP BY 1
ORDER BY 2 DESC
LIMIT 12
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("tool_calls:Q", title="Tool calls"),
    y=alt.Y("tool_name:N", sort="-x", title="Tool"),
    tooltip=["tool_name:N", alt.Tooltip("tool_calls:Q", format=",")]
).properties(title="Most-used tools")
```

## Chart 6: Activity by Project
question: Which projects generated the most sessions and logs?
type: grouped bar
x: project
y: metric value
source: logs

```sql
WITH project_activity AS (
    SELECT
        REGEXP_EXTRACT(cwd, '[^/]+$') AS project,
        COUNT(*) AS logs,
        COUNT(DISTINCT session_id) AS sessions
    FROM logs
    GROUP BY 1
)
SELECT project, metric, value
FROM project_activity
UNPIVOT (value FOR metric IN (logs, sessions))
ORDER BY project, metric
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("project:N", title="Project"),
    y=alt.Y("value:Q", title="Count"),
    color=alt.Color("metric:N", title="Metric"),
    xOffset="metric:N",
    tooltip=["project:N", "metric:N", alt.Tooltip("value:Q", format=",")]
).properties(title="Project activity")
```

## Chart 7: Activity by Git Branch
question: How was activity distributed across Git branches?
type: bar
x: count(logs)
y: git_branch
source: logs

```sql
SELECT git_branch, COUNT(*) AS logs
FROM logs
GROUP BY 1
ORDER BY 2 DESC
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("logs:Q", title="Log records"),
    y=alt.Y("git_branch:N", sort="-x", title="Git branch"),
    tooltip=["git_branch:N", alt.Tooltip("logs:Q", format=",")]
).properties(title="Activity by Git branch")
```

## Chart 8: Session Size Distribution
question: What is the distribution of session sizes?
type: bar
x: session-size bucket
y: count(sessions)
source: logs

```sql
WITH session_sizes AS (
    SELECT session_id, COUNT(*) AS logs_per_session
    FROM logs
    GROUP BY 1
), bucketed AS (
    SELECT
        CASE
            WHEN logs_per_session <= 3 THEN '1–3'
            WHEN logs_per_session <= 6 THEN '4–6'
            WHEN logs_per_session <= 10 THEN '7–10'
            WHEN logs_per_session <= 15 THEN '11–15'
            ELSE '16+'
        END AS session_size,
        CASE
            WHEN logs_per_session <= 3 THEN 1
            WHEN logs_per_session <= 6 THEN 2
            WHEN logs_per_session <= 10 THEN 3
            WHEN logs_per_session <= 15 THEN 4
            ELSE 5
        END AS bucket_order
    FROM session_sizes
)
SELECT session_size, bucket_order, COUNT(*) AS sessions
FROM bucketed
GROUP BY 1, 2
ORDER BY bucket_order
```

```altair
alt.Chart(df).mark_bar().encode(
    x=alt.X("session_size:O", sort=alt.SortField("bucket_order"), title="Logs per session"),
    y=alt.Y("sessions:Q", title="Sessions"),
    tooltip=["session_size:O", alt.Tooltip("sessions:Q", format=",")]
).properties(title="Session size distribution")
```
