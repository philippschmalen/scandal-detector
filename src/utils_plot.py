import numpy as np
import pandas as pd
import plotly.graph_objects as go


def df_plotly_timeline(df_pred: pd.DataFrame, keep_topn_scandals: int) -> pd.DataFrame:
    # marker size for plotly: error
    df_pred["marker_size"] = df_pred["error"].apply(lambda x: x if x > 0 else 5)

    # if row not among nlargest topn_scandals, replace with nan
    df_pred.loc[
        df_pred.index.difference(df_pred.nlargest(keep_topn_scandals, "error").index),
        "label_google_link",
    ] = np.nan

    return df_pred


def plotly_timeline(
    df_pred: pd.DataFrame, keyword_userinput: str, keep_topn_scandals: int
) -> go.Figure:

    df_pred = df_plotly_timeline(df_pred, keep_topn_scandals=keep_topn_scandals)

    fig = go.Figure(
        go.Scatter(
            x=df_pred.ds,
            y=df_pred.y,
            text=df_pred.label_google_link,
            mode="markers+text",
            textposition="middle center",
            marker=dict(
                color=df_pred.outlier.map({1: "#ff6692", 0: "rgba(171, 183, 183, 1)"}),
                size=df_pred.marker_size,  # .map({1: 20, 0: 5}),
            ),
        )
    )

    prediction_color = "#0072B2"
    error_color = "rgba(0, 114, 178, 0.2)"  # '#0072B2' with 0.2 opacity

    # prediction
    # line
    fig.add_trace(
        go.Scatter(
            # name="Predicted",
            x=df_pred.ds,
            y=df_pred.yhat,
            mode="lines",
            line=dict(color=prediction_color, width=3),
            fillcolor=error_color,
            fill="tonexty",
        )
    )
    # upper bound
    fig.add_trace(
        go.Scatter(
            x=df_pred["ds"],
            y=df_pred["yhat_lower"],
            mode="lines",
            line=dict(width=0),
            hoverinfo="skip",
        )
    )
    # lower bound
    fig.add_trace(
        go.Scatter(
            x=df_pred["ds"],
            y=df_pred["yhat_upper"],
            mode="lines",
            line=dict(width=0),
            fillcolor=error_color,
            fill="tonexty",
            hoverinfo="skip",
        )
    )

    fig.update_layout(
        title=f"Scandal detection for '{keyword_userinput}'<br><sup>Found {df_pred.query('outlier == 1').shape[0]} major public scandals within the last 5 years. Top 3 linked to Google.</sup>",
        showlegend=False,
        yaxis_title="Google search interest",
    )

    return fig
