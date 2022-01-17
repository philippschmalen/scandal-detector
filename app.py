import logging
import streamlit as st
from src.utils_data import get_google_trends_firm_scandal
from src.utils_data import get_google_search_url

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

dict_countries = {
    "DE": "skandal",
    "US": "scandal",
    "GLOBAL": "scandal",
}

detector_sensitivity = 0.999
keyword_userinput = st.text_input("Enter a firm name:", "adidas")

select_geo = st.selectbox(label="Select a country", options=dict_countries)
keyword_esg = dict_countries[select_geo]


if st.button("Detect scandals"):
    with st.spinner("Fetching data..."):
        df = get_google_trends_firm_scandal(
            keyword_userinput, keyword_esg=keyword_esg, geo=select_geo
        )

        if df is None:
            st.info(f"No public scandals found on {keyword_userinput}.")
        else:
            google_urls = get_google_search_url(
                df, detector_sensitivity=detector_sensitivity, geo=select_geo
            )
            st.info(
                f"Found {len(google_urls)} public scandal(s) within the last 5 years.\nMost recent first."
            )
            st.balloons()

            for url in google_urls:
                st.markdown(url)
