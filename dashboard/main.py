"""Performance analysis"""

import streamlit as st
import accounting_app
import analysis_app
import ppc_optimizer_app
import clients_app
import keywords_app


# App configuration
st.set_page_config(
    page_title="Amazon FBA Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

hide_streamlit_style = """
    <style>
    footer {visibility: hidden;}
    </style>
"""

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# st.plotly_chart(product.analysis(initial_number_units=504, month=Month.AUGUST))
apps = {
    "Accounting": accounting_app.app,
    "Performance Analysis": analysis_app.app,
    "PPC Optimizer": ppc_optimizer_app.app,
    "Clients Database": clients_app.app,
    "Keywords Repository": keywords_app.app,
}

_, col, _ = st.columns((0.4, 1.0, 0.4))
with col:
    for _ in range(2):
        st.write("")

    app = st.selectbox(
        "Navigation",
        options=list(apps.keys()),
    )

# Run app
apps[app]()










        