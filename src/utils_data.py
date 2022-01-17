import pandas as pd
import logging
from functools import wraps
from prophet import Prophet
from pytrends.request import TrendReq


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


def column_add_outlier(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates outlier column for prophet forecast
    outlier: greater than yhat_upper, ignore lower than yhat_lower
    """

    df["outlier"] = ((df["yhat_upper"] > df.y)).astype("uint8")

    return df


def merge_forecast_and_history(m: Prophet, forecast: pd.DataFrame) -> pd.DataFrame:
    return forecast.merge(m.history, on="ds", how="left")


def create_google_search_url(df: pd.DataFrame, geo: str) -> pd.DataFrame:
    "Create google search url for a keyword and date + 7 days"

    dict_geo = {
        "US": "com",
        "DE": "de",
        "GLOBAL": "com",
    }

    df["google_search_url"] = (
        f"https://www.google.{dict_geo[geo]}/search?q="
        + df.keyword_google
        + "+after:"
        + df.date.astype(str)
        + "+before:"
        + df.date_plus_7.astype(str)
    )

    return df


def get_google_search_url(
    df: pd.DataFrame, detector_sensitivity=0.99, geo="US"
) -> list:
    "Detector outlier on google trends time series and create google search url"

    m = Prophet(
        interval_width=detector_sensitivity,
        weekly_seasonality=False,
        yearly_seasonality=True,
        daily_seasonality=False,
    )
    m.fit(df)
    forecast = m.predict(m.make_future_dataframe(periods=0))

    return (
        merge_forecast_and_history(m, forecast)
        .pipe(column_add_outlier)
        .query("outlier == 1")
        .assign(
            date_plus_7=lambda x: x["date"] + pd.Timedelta(days=30),
            keyword_google=lambda x: x["keyword"].apply(lambda s: "+".join(s.split())),
        )
        .pipe(create_google_search_url, geo=geo)
    ).google_search_url.to_list()[::-1]


def get_google_trends_firm_scandal(
    keyword_userinput: str, keyword_esg: str = "scandal", geo: str = "US"
) -> pd.DataFrame:
    keyword_searchtrends = keyword_userinput.strip() + f" {keyword_esg}"

    if geo == "GLOBAL":
        geo = ""

    pt = TrendReq()
    pt.build_payload(kw_list=[keyword_searchtrends], geo=geo)
    df_raw = pt.interest_over_time()

    if len(df_raw) > 0:
        return df_raw.pipe(process_interest_over_time).pipe(preprocessing)
    else:
        logging.info(f"No results found. get_google_trends_firm_scandal returns None.")
        return None
