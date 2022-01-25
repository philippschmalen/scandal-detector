import logging
import streamlit as st
from prophet import Prophet
import pandas as pd
from src.utils_data import get_google_trends_firm_scandal
from src.utils_data import get_df_pred
from src.utils_data import get_list_of_scandal_links
from src.utils_plot import plotly_timeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# CONFIG
detector_sensitivity = 0.99
date_uppderbound_days = 30
keep_topn_scandals = 3

dict_geo = {
    "DE": {"domain": "de", "keyword": "Skandal", "gtrends": "DE"},
    "US": {"domain": "com", "keyword": "scandal", "gtrends": "US"},
    "FR": {"domain": "fr", "keyword": "scandale", "gtrends": "FR"},
    "GLOBAL": {"domain": "com", "keyword": "scandal", "gtrends": ""},
}


# SELECTIONS
st.title("Scandal Detector")
st.subheader("Search major scandals for publicly known companies")

keyword_userinput = st.text_input(label="Enter a firm name:", value="deutsche bank")
select_geo = st.selectbox(label="Select a country", options=dict_geo)

# ------------------------------------------
# TEST DATA
# keyword_userinput = "deutsche bank"
# filepath_mockdata = "data/test/mockdata_deutschebank.csv"

# if st.sidebar.button("Get fresh Google Trends"):
#     df_raw = get_google_trends_firm_scandal(keyword_userinput)
#     df = df_raw.copy()
#     st.info(f"Got google trends for {keyword_userinput} with {len(df)} rows")
# else:
#     df = pd.read_csv(filepath_mockdata, parse_dates=["date", "ds"])
#     st.info("Loaded mock data")
# ------------------------------------------


# MAIN
if st.button("Detect scandals"):
    with st.spinner("Fetching data..."):
        df = get_google_trends_firm_scandal(
            keyword_userinput, dict_domain_keyword=dict_geo[select_geo]
        )

        if df is None:
            st.info(f"No public scandals found for {keyword_userinput}.")
        else:
            df_pred = get_df_pred(
                df,
                detector_sensitivity,
                date_uppderbound_days,
                dict_domain_keyword=dict_geo[select_geo],
            )

            st.info(
                f"Found {len(df_pred.query('outlier == 1'))} major public scandal(s) within the last 5 years."
            )
            st.subheader("Timeline on scandals over last 5 years")
            fig = plotly_timeline(df_pred.copy(), keyword_userinput, keep_topn_scandals)
            st.plotly_chart(fig)

            st.subheader("Scandals sorted by severity")

            # write links as list
            st.write(
                get_list_of_scandal_links(df_pred).to_html(escape=False, index=False),
                unsafe_allow_html=True,
            )

st.write("---")
st.image("img/tsf_logo.png")
