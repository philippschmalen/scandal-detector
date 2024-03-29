import logging
import streamlit as st
from src.utils_data import get_google_trends_firm_scandal
from src.utils_data import get_df_pred
from src.utils_data import get_list_of_scandal_links
from src.utils_data import hide_streamlit_style
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
    "FI": {"domain": "fi", "keyword": "skandaali", "gtrends": "FI"},
    "GLOBAL": {"domain": "com", "keyword": "scandal", "gtrends": ""},
}


st.title("Scandal Detector")
st.subheader("Identify public scandals of a well-known company")

# SELECTIONS
keyword_userinput = st.text_input(label="Enter a firm name:", value="deutsche bank")
select_geo = st.selectbox(label="Select a country", options=dict_geo)


if st.button("Detect scandals ↓"):
    with st.spinner("Fetching data... ↓↓↓"):
        # get data
        df = get_google_trends_firm_scandal(
            keyword_userinput, dict_domain_keyword=dict_geo[select_geo]
        )

        if df is None:
            st.info(f"No public scandals found for {keyword_userinput}.")

        else:
            # predict
            df_pred = get_df_pred(
                df,
                detector_sensitivity,
                date_uppderbound_days,
                dict_domain_keyword=dict_geo[select_geo],
            )

            st.info(
                f"Found {len(df_pred.query('outlier == 1'))} major public scandal(s) within the last 5 years."
            )

            # plot
            st.subheader("Timeline on scandals over last 5 years")
            fig = plotly_timeline(df_pred.copy(), keyword_userinput, keep_topn_scandals)
            st.plotly_chart(fig)

            st.subheader("Scandals sorted by severity")

            # list
            st.write(
                get_list_of_scandal_links(df_pred).to_html() + "<br>",
                unsafe_allow_html=True,
            )


with st.expander("How it works"):
    """
    The scandal detector uses search interest from Google trends and applies a time-series model to identify public scandals. It searches for "keyword + scandal" in the selected language and Google domain, such as google.de or google.com. If search interest lies far outside of what is expected (=model's prediction), we define this as a scandal. *Scandal severity* is defined as the difference between the actual search interest and the predicted search interest. The larger the difference to what we expect, the more public attention the scandal received.

    Here is the data flow:
    """
    st.image("img/data-flow.png")
    """
    The app runs on `streamlit`. When you click `detect scandals` it launches `pytrends` to get research interest of the given keyword plus the word 'scandal' in the selected language. The raw data gets processed within `pandas` to be ready for `facebook prophet` and generate Google search links in HTML. The time-series model trains on the whole data and predicts the search interest. This prediction is the expected search interest. If the actual search interest of "keyword+scandal" lies far from what is expected, this is defined as a public scandal. Lastly,`plotly` visualizes the timeline including actual search interest, predicted search interest and scandals.

    **Note**: The process works for well-known public entities. It requires a substantial number of searches to be visible in Google Trends data.

    ---

    You can access the source code on https://github.com/philippschmalen/scandal-detector. Feel free to contribute!

    If you have made it so far, I would love ot hear from you. Drop me a line on [linkedin](https://www.linkedin.com/in/philippschmalen/).
    """

st.markdown(hide_streamlit_style(), unsafe_allow_html=True)
