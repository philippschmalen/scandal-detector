import logging
import streamlit as st
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


st.title("Scandal Detector")
st.subheader("Identify major public scandals of a company")

# SELECTIONS
keyword_userinput = st.text_input(label="Enter a firm name:", value="deutsche bank")
select_geo = st.selectbox(label="Select a country", options=dict_geo)

# DATA PIPELINE
if st.button("Detect scandals"):
    with st.spinner("Fetching data..."):
        # fetch google trends
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

            # PLOT
            st.subheader("Timeline on scandals over last 5 years")
            fig = plotly_timeline(df_pred.copy(), keyword_userinput, keep_topn_scandals)
            st.plotly_chart(fig)

            st.subheader("Scandals sorted by severity")

            # link list
            st.write(
                get_list_of_scandal_links(df_pred).to_html(escape=False, index=False),
                unsafe_allow_html=True,
            )


with st.expander("See how it works"):
    """
    The scandal detector uses search interest from Google trends and applies a time-series model to identify public scandals.
    """
    st.image("img/data-flow.png")
    """
    You can access the source code on https://github.com/philippschmalen/scandal-detector. Feel free to contribute!

    If you have made it so far, I would love ot hear from you. Drop me a line on [linkedin](https://www.linkedin.com/in/philippschmalen/).
    """

st.write("---")
st.image("img/tsf_logo.png")
