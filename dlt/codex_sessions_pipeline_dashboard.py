import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")


@app.cell
def _():
    import altair as alt
    import dlt
    import marimo as mo

    return alt, dlt, mo


@app.cell
def _(mo):
    mo.md("""
    # Codex CLI usage report

    Aggregate usage metadata from `codex_sessions_pipeline.raw_session_events`.
    All JSON fields are extracted in DuckDB SQL; message and reasoning text are
    intentionally excluded. Times are UTC.
    """)
    return


@app.cell
def _(dlt):
    pipeline = dlt.attach("codex_sessions_pipeline")
    dataset = pipeline.dataset()
    return (dataset,)


@app.cell
def _(mo):
    mo.md("""
    ## Activity and record composition
    """)
    return


@app.cell
def _(dataset):
    df_chart1 = dataset(
        """
        SELECT DATE_TRUNC('minute', timestamp) AS activity_minute,
               record_type, COUNT(*) AS records
        FROM raw_session_events
        GROUP BY 1, 2
        ORDER BY 1, 2
        """
    ).df()
    return (df_chart1,)


@app.cell
def _(alt, df_chart1):
    _chart = alt.Chart(df_chart1).mark_line(point=True).encode(
        x=alt.X("activity_minute:T", title="Activity minute (UTC)"),
        y=alt.Y("records:Q", title="Records"),
        color=alt.Color("record_type:N", title="Record type"),
        tooltip=["activity_minute:T", "record_type:N", "records:Q"],
    ).properties(title="Codex CLI activity by minute", height=300)
    _chart
    return


@app.cell
def _(dataset):
    df_chart2 = dataset(
        """
        SELECT record_type, COUNT(*) AS records
        FROM raw_session_events
        GROUP BY 1
        ORDER BY 2 DESC
        """
    ).df()
    return (df_chart2,)


@app.cell
def _(alt, df_chart2):
    _chart = alt.Chart(df_chart2).mark_bar().encode(
        x=alt.X("records:Q", title="Records"),
        y=alt.Y("record_type:N", sort="-x", title="Record type"),
        tooltip=["record_type:N", "records:Q"],
    ).properties(title="Records by type", height=220)
    _chart
    return


@app.cell
def _(mo):
    mo.md("""
    ## Event and response structure
    """)
    return


@app.cell
def _(dataset):
    df_chart3 = dataset(
        """
        SELECT COALESCE(json_extract_string(raw_json, '$.payload.type'), '(unavailable)') AS event_subtype,
               COUNT(*) AS records
        FROM raw_session_events
        WHERE record_type = 'event_msg'
        GROUP BY 1
        ORDER BY 2 DESC
        """
    ).df()
    return (df_chart3,)


@app.cell
def _(alt, df_chart3):
    _chart = alt.Chart(df_chart3).mark_bar().encode(
        x=alt.X("records:Q", title="Event messages"),
        y=alt.Y("event_subtype:N", sort="-x", title="Event subtype"),
        tooltip=["event_subtype:N", "records:Q"],
    ).properties(title="event_msg subtypes", height=280)
    _chart
    return


@app.cell
def _(dataset):
    df_chart4 = dataset(
        """
        SELECT COALESCE(json_extract_string(raw_json, '$.payload.type'), '(unavailable)') AS response_subtype,
               COALESCE(json_extract_string(raw_json, '$.payload.role'), '(not applicable)') AS role,
               COUNT(*) AS records
        FROM raw_session_events
        WHERE record_type = 'response_item'
        GROUP BY 1, 2
        ORDER BY 1, 2
        """
    ).df()
    return (df_chart4,)


@app.cell
def _(alt, df_chart4):
    _chart = alt.Chart(df_chart4).mark_bar().encode(
        x=alt.X("records:Q", title="Response items", stack="zero"),
        y=alt.Y("response_subtype:N", title="Response subtype"),
        color=alt.Color("role:N", title="Role"),
        tooltip=["response_subtype:N", "role:N", "records:Q"],
    ).properties(title="response_item subtype and role", height=240)
    _chart
    return


@app.cell
def _(mo):
    mo.md("""
    ## Tokens and models

    Token counters are available. The chart uses the latest cumulative snapshot
    per session, rather than summing snapshots. Cached input is part of input;
    reasoning output is part of output, so the displayed counters overlap.
    """)
    return


@app.cell
def _(dataset):
    df_chart5 = dataset(
        """
        WITH token_snapshots AS (
            SELECT source_path, timestamp,
                   TRY_CAST(json_extract_string(raw_json, '$.payload.info.total_token_usage.input_tokens') AS BIGINT) AS input_tokens,
                   TRY_CAST(json_extract_string(raw_json, '$.payload.info.total_token_usage.cached_input_tokens') AS BIGINT) AS cached_input_tokens,
                   TRY_CAST(json_extract_string(raw_json, '$.payload.info.total_token_usage.output_tokens') AS BIGINT) AS output_tokens,
                   TRY_CAST(json_extract_string(raw_json, '$.payload.info.total_token_usage.reasoning_output_tokens') AS BIGINT) AS reasoning_output_tokens,
                   TRY_CAST(json_extract_string(raw_json, '$.payload.info.total_token_usage.total_tokens') AS BIGINT) AS total_tokens
            FROM raw_session_events
            WHERE record_type = 'event_msg'
              AND json_extract_string(raw_json, '$.payload.type') = 'token_count'
        ), latest AS (
            SELECT REGEXP_EXTRACT(source_path, '[^/]+$') AS session,
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
        UNPIVOT (token_count FOR metric IN
            (total_tokens, input_tokens, cached_input_tokens, output_tokens, reasoning_output_tokens))
        ORDER BY session, metric
        """
    ).df()
    return (df_chart5,)


@app.cell
def _(alt, df_chart5):
    _chart = alt.Chart(df_chart5).mark_bar().encode(
        x=alt.X("metric:N", title="Cumulative counter"),
        y=alt.Y("token_count:Q", title="Tokens"),
        color=alt.Color("session:N", title="Session file"),
        xOffset="session:N",
        tooltip=["session:N", "metric:N", alt.Tooltip("token_count:Q", format=",")],
    ).properties(title="Latest cumulative token counters per session", height=320)
    _chart
    return


@app.cell
def _(dataset):
    df_chart6 = dataset(
        """
        SELECT COALESCE(json_extract_string(raw_json, '$.payload.model'), '(unavailable)') AS model,
               COUNT(DISTINCT json_extract_string(raw_json, '$.payload.turn_id')) AS turns
        FROM raw_session_events
        WHERE record_type = 'turn_context'
        GROUP BY 1
        ORDER BY 2 DESC
        """
    ).df()
    return (df_chart6,)


@app.cell
def _(alt, df_chart6):
    _chart = alt.Chart(df_chart6).mark_bar().encode(
        x=alt.X("model:N", title="Model"),
        y=alt.Y("turns:Q", title="Distinct turns"),
        tooltip=["model:N", "turns:Q"],
    ).properties(title="Model usage by turn", height=240)
    _chart
    return


@app.cell
def _(mo):
    mo.md("""
    ## Projects, sessions, and turns

    No explicit project name exists. Working directory is labeled as the
    available project proxy. Sessions use `session_meta.payload.id`; turns use
    distinct `turn_context.payload.turn_id`.
    """)
    return


@app.cell
def _(dataset):
    df_chart7 = dataset(
        """
        SELECT COALESCE(json_extract_string(raw_json, '$.payload.cwd'), '(unavailable)') AS working_directory,
               COUNT(DISTINCT json_extract_string(raw_json, '$.payload.turn_id')) AS turns
        FROM raw_session_events
        WHERE record_type = 'turn_context'
        GROUP BY 1
        ORDER BY 2 DESC
        """
    ).df()
    return (df_chart7,)


@app.cell
def _(alt, df_chart7):
    _chart = alt.Chart(df_chart7).mark_bar().encode(
        x=alt.X("turns:Q", title="Distinct turns"),
        y=alt.Y("working_directory:N", sort="-x", title="Working directory (project proxy)"),
        tooltip=["working_directory:N", "turns:Q"],
    ).properties(title="Turns by working directory", height=220)
    _chart
    return


@app.cell
def _(dataset):
    df_chart8 = dataset(
        """
        SELECT 'Sessions' AS metric,
               COUNT(DISTINCT json_extract_string(raw_json, '$.payload.id')) AS count
        FROM raw_session_events
        WHERE record_type = 'session_meta'
        UNION ALL
        SELECT 'Turns' AS metric,
               COUNT(DISTINCT json_extract_string(raw_json, '$.payload.turn_id')) AS count
        FROM raw_session_events
        WHERE record_type = 'turn_context'
        """
    ).df()
    return (df_chart8,)


@app.cell
def _(alt, df_chart8):
    _chart = alt.Chart(df_chart8).mark_bar().encode(
        x=alt.X("metric:N", title=None),
        y=alt.Y("count:Q", title="Count"),
        color=alt.Color("metric:N", legend=None),
        tooltip=["metric:N", "count:Q"],
    ).properties(title="Available session and turn counts", height=240)
    _chart
    return


if __name__ == "__main__":
    app.run()
