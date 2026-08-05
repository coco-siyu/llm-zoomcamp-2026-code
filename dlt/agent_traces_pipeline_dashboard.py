import marimo

__generated_with = "0.23.16"
app = marimo.App(width="full")


@app.cell
def _():
    import altair as alt
    import dlt
    import marimo as mo

    return alt, dlt, mo


@app.cell
def _(mo):
    mo.md("""
    # Agent traces usage report

    A Codex-usage-style view of **20,000 Claude Code agent logs** loaded by
    `agent_traces_pipeline`. Metrics are aggregated and times are UTC; message
    text, tool inputs, UUIDs, and session identifiers are intentionally hidden.
    """)
    return


@app.cell
def _(dlt):
    dataset = dlt.dataset(
        destination="playground",
        dataset_name="agent_traces_data",
    )
    return (dataset,)


@app.cell
def _(dataset):
    kpi_df = dataset("""
        SELECT
            COUNT(*) AS logs,
            COUNT(DISTINCT session_id) AS sessions,
            COUNT(DISTINCT REGEXP_EXTRACT(cwd, '[^/]+$')) AS projects,
            SUM(COALESCE(usage__input_tokens, 0)) AS input_tokens,
            SUM(COALESCE(usage__output_tokens, 0)) AS output_tokens
        FROM logs
    """).df()
    return (kpi_df,)


@app.cell
def _(kpi_df, mo):
    _k = kpi_df.iloc[0]
    _cards = [
        ("Logs", f"{int(_k.logs):,}"),
        ("Sessions", f"{int(_k.sessions):,}"),
        ("Projects", f"{int(_k.projects):,}"),
        ("Input tokens", f"{int(_k.input_tokens):,}"),
        ("Output tokens", f"{int(_k.output_tokens):,}"),
    ]
    mo.hstack(
        [
            mo.md(
                f"""<div style="padding:1rem;border:1px solid #e5e7eb;
                border-radius:12px;background:#fafafa;min-width:150px">
                <div style="font-size:.8rem;color:#64748b">{label}</div>
                <div style="font-size:1.55rem;font-weight:700">{value}</div>
                </div>"""
            )
            for label, value in _cards
        ],
        justify="space-between",
        gap=1,
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ## Activity and token usage
    """)
    return


@app.cell
def _(dataset):
    df_chart1 = dataset("""
        SELECT DATE_TRUNC('hour', timestamp) AS activity_hour,
               type, COUNT(*) AS logs
        FROM logs
        GROUP BY 1, 2
        ORDER BY 1, 2
    """).df()
    return (df_chart1,)


@app.cell
def _(alt, df_chart1):
    _chart = alt.Chart(df_chart1).mark_area(opacity=0.72).encode(
        x=alt.X("activity_hour:T", title="Hour (UTC)"),
        y=alt.Y("logs:Q", title="Log records", stack="zero"),
        color=alt.Color("type:N", title="Message type"),
        tooltip=["activity_hour:T", "type:N", alt.Tooltip("logs:Q", format=",")],
    ).properties(title="Agent activity by hour", height=300)
    _chart
    return


@app.cell
def _(dataset):
    df_chart2 = dataset("""
        WITH hourly AS (
            SELECT DATE_TRUNC('hour', timestamp) AS activity_hour,
                   SUM(COALESCE(usage__input_tokens, 0)) AS input_tokens,
                   SUM(COALESCE(usage__output_tokens, 0)) AS output_tokens
            FROM logs
            GROUP BY 1
        )
        SELECT activity_hour, token_type, tokens
        FROM hourly
        UNPIVOT (tokens FOR token_type IN (input_tokens, output_tokens))
        ORDER BY activity_hour, token_type
    """).df()
    return (df_chart2,)


@app.cell
def _(alt, df_chart2):
    _chart = alt.Chart(df_chart2).mark_line(point=True).encode(
        x=alt.X("activity_hour:T", title="Hour (UTC)"),
        y=alt.Y("tokens:Q", title="Tokens"),
        color=alt.Color("token_type:N", title="Token type"),
        tooltip=["activity_hour:T", "token_type:N", alt.Tooltip("tokens:Q", format=",")],
    ).properties(title="Hourly token usage", height=300)
    _chart
    return


@app.cell
def _(mo):
    mo.md("""
    ## Models and messages
    """)
    return


@app.cell
def _(dataset):
    df_chart3 = dataset("""
        WITH model_tokens AS (
            SELECT message__model AS model,
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
    """).df()
    return (df_chart3,)


@app.cell
def _(alt, df_chart3):
    _chart = alt.Chart(df_chart3).mark_bar().encode(
        x=alt.X("model:N", title="Model", sort="-y"),
        y=alt.Y("tokens:Q", title="Tokens", stack="zero"),
        color=alt.Color("token_type:N", title="Token type"),
        tooltip=["model:N", "token_type:N", alt.Tooltip("tokens:Q", format=",")],
    ).properties(title="Token usage by model", height=300)
    _chart
    return


@app.cell
def _(dataset):
    df_chart4 = dataset("""
        SELECT type, COUNT(*) AS logs
        FROM logs
        GROUP BY 1
        ORDER BY 2 DESC
    """).df()
    return (df_chart4,)


@app.cell
def _(alt, df_chart4):
    _chart = alt.Chart(df_chart4).mark_bar(
        cornerRadiusTopLeft=5, cornerRadiusTopRight=5
    ).encode(
        x=alt.X("type:N", title="Message type"),
        y=alt.Y("logs:Q", title="Log records"),
        color=alt.Color("type:N", legend=None),
        tooltip=["type:N", alt.Tooltip("logs:Q", format=",")],
    ).properties(title="User and assistant messages", height=280)
    _chart
    return


@app.cell
def _(dataset):
    df_chart5 = dataset("""
        SELECT name AS tool_name, COUNT(*) AS tool_calls
        FROM logs__message__content
        WHERE type = 'tool_use' AND name IS NOT NULL
        GROUP BY 1
        ORDER BY 2 DESC
        LIMIT 12
    """).df()
    return (df_chart5,)


@app.cell
def _(alt, df_chart5):
    _chart = alt.Chart(df_chart5).mark_bar().encode(
        x=alt.X("tool_calls:Q", title="Tool calls"),
        y=alt.Y("tool_name:N", sort="-x", title="Tool"),
        tooltip=["tool_name:N", alt.Tooltip("tool_calls:Q", format=",")],
    ).properties(title="Most-used tools", height=320)
    _chart
    return


@app.cell
def _(mo):
    mo.md("""
    ## Projects, branches, and sessions
    """)
    return


@app.cell
def _(dataset):
    df_chart6 = dataset("""
        WITH project_activity AS (
            SELECT REGEXP_EXTRACT(cwd, '[^/]+$') AS project,
                   COUNT(*) AS logs,
                   COUNT(DISTINCT session_id) AS sessions
            FROM logs
            GROUP BY 1
        )
        SELECT project, metric, value
        FROM project_activity
        UNPIVOT (value FOR metric IN (logs, sessions))
        ORDER BY project, metric
    """).df()
    return (df_chart6,)


@app.cell
def _(alt, df_chart6):
    _chart = alt.Chart(df_chart6).mark_bar().encode(
        x=alt.X("project:N", title="Project"),
        y=alt.Y("value:Q", title="Count"),
        color=alt.Color("metric:N", title="Metric"),
        xOffset="metric:N",
        tooltip=["project:N", "metric:N", alt.Tooltip("value:Q", format=",")],
    ).properties(title="Project activity", height=300)
    _chart
    return


@app.cell
def _(dataset):
    df_chart7 = dataset("""
        SELECT git_branch, COUNT(*) AS logs
        FROM logs
        GROUP BY 1
        ORDER BY 2 DESC
    """).df()
    return (df_chart7,)


@app.cell
def _(alt, df_chart7):
    _chart = alt.Chart(df_chart7).mark_bar().encode(
        x=alt.X("logs:Q", title="Log records"),
        y=alt.Y("git_branch:N", sort="-x", title="Git branch"),
        tooltip=["git_branch:N", alt.Tooltip("logs:Q", format=",")],
    ).properties(title="Activity by Git branch", height=260)
    _chart
    return


@app.cell
def _(dataset):
    df_chart8 = dataset("""
        WITH session_sizes AS (
            SELECT session_id, COUNT(*) AS logs_per_session
            FROM logs
            GROUP BY 1
        ), bucketed AS (
            SELECT CASE
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
    """).df()
    return (df_chart8,)


@app.cell
def _(alt, df_chart8):
    _chart = alt.Chart(df_chart8).mark_bar().encode(
        x=alt.X(
            "session_size:O",
            sort=alt.SortField("bucket_order"),
            title="Logs per session",
        ),
        y=alt.Y("sessions:Q", title="Sessions"),
        tooltip=["session_size:O", alt.Tooltip("sessions:Q", format=",")],
    ).properties(title="Session size distribution", height=280)
    _chart
    return


if __name__ == "__main__":
    app.run()
