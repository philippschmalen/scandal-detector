import pandas as pd
import logging
from functools import wraps
from prophet import Prophet
from pytrends.request import TrendReq
import streamlit as st


def wrap_logging_transform_df(func):
    """Wrapper to compare df before and after transformation"""

    @wraps(func)
    def with_logging(*args, **kwargs):

        try:
            df_orig: pd.DataFrame = args[0]
            df_edit: pd.DataFrame = func(*args, **kwargs)

            # df_edit and df_orig should be dataframe
            if not isinstance(df_orig, pd.DataFrame):
                raise TypeError(
                    f"{func.__name__} args[0] is not a dataframe, but type: {type(args[0])}). Skip logging."
                )

            if not isinstance(df_edit, pd.DataFrame):
                raise TypeError(
                    f"{func.__name__} did not return dataframe, but type: {type(df_edit)}. Skip logging."
                )

            else:
                logging_transform_df(df_orig, df_edit, func.__name__)
                return df_edit

        except Exception as e:
            logging.error(f"{func.__name__} - wrap_logging_transform_df(): {e}")

        return func(*args, **kwargs)

    return with_logging


def logging_transform_df(
    df_orig: pd.DataFrame, df_edit: pd.DataFrame, step_name: str = "compare df"
) -> None:
    "Logging utility to show row difference between two dataframes"
    N_orig, N_edit = len(df_orig), len(df_edit)
    N_diff = N_orig - N_edit
    pct_diff = N_diff / N_orig * 100

    # sign for added or removed rows
    if N_diff > 0:
        sign = "-"
    if N_diff < 0:
        N_diff *= -1
        pct_diff *= -1
        sign = "+"
    if N_diff == 0:
        sign = ""

    logging.info(
        f"{step_name} --> {sign}{N_diff} records ({sign}{pct_diff:.2f}%, {N_orig}-{N_edit})"
    )


@wrap_logging_transform_df
def drop_missings_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    "Return df without missings and duplicates"
    df_nomiss = df.dropna()
    df_nodup = df_nomiss.drop_duplicates()

    return df_nodup.reset_index(drop=True)


def process_interest_over_time(df: pd.DataFrame) -> pd.DataFrame:
    "Process query results of pytrends interest_over_time()"

    if len(df) > 0:
        df_processed = df.reset_index().drop(["isPartial"], axis=1)

        return pd.melt(
            df_processed,
            id_vars=["date"],
            var_name="keyword",
            value_name="search_interest",
        )

    # no google trend data available
    else:
        logging.info("No results found. process_interest_over_time returns None.")
        return None


@wrap_logging_transform_df
def preprocessing(df: pd.DataFrame) -> pd.DataFrame:
    return df.pipe(drop_missings_duplicates).assign(
        ds=lambda x: x["date"], y=lambda x: x["search_interest"], floor=0, cap=100
    )


def add_column_outlier(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates outlier column for prophet forecast
    outlier: greater than yhat_upper, ignore lower than yhat_lower
    """

    df["outlier"] = ((df.y > df["yhat_upper"])).astype("uint8")

    return df


def merge_forecast_and_history(m: Prophet, forecast: pd.DataFrame) -> pd.DataFrame:
    return forecast.merge(m.history, on="ds", how="left")


def create_google_search_link(
    df: pd.DataFrame, dict_domain_keyword: dict
) -> pd.DataFrame:
    "Create google search url for a keyword and date + upperbound days"

    df["google_search_http"] = (
        f"https://www.google.{dict_domain_keyword['domain']}/search?q="
        + df.keyword_google
        + "+after:"
        + df.date.astype(str)
        + "+before:"
        + df.date_upperbound.astype(str)
    )

    df["label_google_link"] = (
        '<a href="'
        + df["google_search_http"].astype(str)
        + '" target="_blank" rel="noopener noreferrer">'
        + "Google search</a>"
    )

    return df


def add_column_error(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(error=lambda x: x["y"] - x["yhat"])


def add_column_circle(df: pd.DataFrame) -> pd.DataFrame:
    "Degrees in circle for polar plot"
    df["circle"] = pd.Series(range(len(df)), index=df.index) * 360 / len(df)
    return df


def get_df_pred(
    df: pd.DataFrame,
    detector_sensitivity: float,
    date_uppderbound_days: int,
    dict_domain_keyword: dict,
) -> pd.DataFrame:
    # PREDICTION pipeline: df --> m, forecast
    m = Prophet(
        interval_width=detector_sensitivity,
        weekly_seasonality=False,
        yearly_seasonality=True,
        daily_seasonality=False,
    )
    m.fit(df)
    forecast = m.predict(m.make_future_dataframe(periods=0))

    # process forecast --> df_pred
    return (
        merge_forecast_and_history(m, forecast)
        .pipe(add_column_outlier)
        .assign(
            date_upperbound=lambda x: x["date"]
            + pd.Timedelta(days=date_uppderbound_days),
            keyword_google=lambda x: x["keyword"].apply(lambda s: "+".join(s.split())),
        )
        .pipe(create_google_search_link, dict_domain_keyword)
        .pipe(add_column_error)
        .pipe(add_column_circle)
    )


@st.cache_data
def get_google_trends_firm_scandal(
    keyword_userinput: str, dict_domain_keyword: dict
) -> pd.DataFrame:
    keyword_searchtrends = (
        keyword_userinput.strip() + f" {dict_domain_keyword['keyword']}"
    )

    pt = TrendReq()
    pt.build_payload(kw_list=[keyword_searchtrends], geo=dict_domain_keyword["gtrends"])
    df_raw = pt.interest_over_time()

    if len(df_raw) > 0:
        return df_raw.pipe(process_interest_over_time).pipe(preprocessing)
    else:
        logging.info("No results found. get_google_trends_firm_scandal returns None.")
        return None


def get_list_of_scandal_links(df):
    return (
        df.query("outlier == 1")
        .loc[:, ["date", "error", "label_google_link"]]
        # error as int, date format as yyyy-mm-dd
        .astype({"error": "int32", "date": "str"})
        .rename(
            {
                "date": "Date",
                "error": "Scandal severity",
                "label_google_link": "Link to Google",
            },
            axis=1,
        )
        .sort_values(by="Scandal severity", ascending=False)
        .pipe(style_df)
    )


def style_df(df):
    styler = df.style
    styler.background_gradient(vmin=20, vmax=100, cmap="OrRd")
    styler.hide(axis="index")
    return styler


def hide_streamlit_style() -> str:
    return """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """
