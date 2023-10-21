import streamlit as st
import pandas as pd
import json
import plotly.figure_factory as ff
import folium
from streamlit_folium import st_folium

def app():
    # Orders Report
    report = st.file_uploader(
        "Upload Fullfilment Report", 
        type=[".txt"]
    )
    if report:
        df_orders = pd.read_csv(report, sep="\t").query("`order-status` == 'Shipped'")
        df_orders["COUNTER"] = 1
        st.write(df_orders)

        df_fips = pd.read_csv(
            "fips2county.tsv", 
            sep='\t', 
            header='infer', 
            dtype=str, 
            encoding='latin-1',
        )

        def find_fips(x) -> str:
            state = x["ship-state"]

            if state.capitalize() in df_fips["StateName"].values:
                state = state.capitalize()
                return df_fips.query("StateName == @state").reset_index().loc[0]["CountyFIPS"]
            elif state in df_fips["StateAbbr"].values:
                return df_fips.query("StateAbbr == @state").reset_index().loc[0]["CountyFIPS"]
            else:
                return None
            
        df_orders["FIPS"] = df_orders.apply(find_fips, axis=1)

        df_orders = df_orders.dropna(subset=['FIPS'])

        df_orders["COUNTER"] = 1

    
        # initialize the map and store it in a m object
        m = folium.Map(location=[40, -95], zoom_start=3)

        

        url = (
            "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data"
        )
        state_geo = f"{url}/us-states.json"

        state_data = df_orders.groupby("ship-state").sum().reset_index()[["ship-state", "COUNTER"]]

        folium.Choropleth(
            geo_data=state_geo,
            name="choropleth",
            data=state_data,
            columns=["ship-state", "COUNTER"],
            key_on="feature.id",
            fill_color="YlGn",
            fill_opacity=0.7,
            line_opacity=.1,
            legend_name="Number of Orders",
        ).add_to(m)

        folium.LayerControl().add_to(m)

        # show the map
        st_folium(m, width=1000)
