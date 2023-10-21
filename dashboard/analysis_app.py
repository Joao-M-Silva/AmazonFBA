import streamlit as st
import pandas as pd
from typing import List
from utils import (load_products, 
                   dump_products, 
                   load_performance_data,
                   dump_performance_data,
                   instantiate_product, 
                   product_display)
from analysis import PPCAnalysis, PerformanceAnalysis, DateRange
from products.utils import Product
from reports_analyser import (BusinessReportAnalyser, 
                              CampaignReportAnalyser, 
                              DailyPerformanceReportAnalyser, 
                              Reports)


def app():

    if "products" not in st.session_state:
        st.session_state["products"] : List[Product] = load_products(path="products/products.json")
    
    if "performance_data" not in st.session_state:
        st.session_state["performance_data"] : List[dict] = load_performance_data("performance_data.json")

    with st.sidebar:
        st.write("- Number Products: ", len(st.session_state["products"]))
        products_names = [p.name for p in st.session_state["products"]]
        product_name = st.selectbox(
            "Select the product",
            options=products_names,
        )
        
        product_index = products_names.index(product_name)
        product = st.session_state["products"][product_index]
        
        product_display(product)

        add_new_product = st.checkbox("Add new product")
        if add_new_product:
            product_to_add = instantiate_product()
            if product_to_add is not None:
                st.session_state["products"].append(product_to_add)
                dump_products(st.session_state["products"], "products/products.json")
                st.experimental_rerun()

        update_product = st.checkbox("Update Current Product")
        if update_product:
            updated_product = instantiate_product(product=product)
            if updated_product is not None:
                st.session_state["products"][product_index] = updated_product
                dump_products(st.session_state["products"], "products/products.json")
                st.experimental_rerun()


    st.title("Daily Sales and Traffic Analysis")
    st.subheader("Read Sales and Traffic Business Report")
    business_report = st.file_uploader("Upload Business Report", type=[".csv"])
    if business_report:
        BusinessReportAnalyser().show(business_report)

    st.write("***")

    st.title("Daily Sponsored Products Performance Analysis")
    st.subheader("Read Sponsored Products Daily Campaign Report")
    st.write("Steps: ")
    st.write("- 1: Go Amazon Ads Reports Section")
    st.write("- 2: Select 'Sponsored Products' in the 'Report category'")
    st.write("- 3: Select 'Campaign' in the 'Report type'")
    st.write("- 4: Select 'Daily' in the 'Time unit'")
    campaign_report = st.file_uploader("Upload Campaign Report", type=[".csv"])
    if campaign_report:
        CampaignReportAnalyser(tax=0.23).show(campaign_report)

    st.write("***")

    st.title("Daily Performance Analysis")
    st.subheader("Read Sales and Traffic Business Report")
    with st.form("daily-reports"):
        business_report_d = st.file_uploader("Upload Business Report", type=[".csv"])
        campaign_report_d = st.file_uploader("Upload Campaign Report", type=[".csv"])
        referal_fee_percentage = st.number_input("Referal Fee Percentage", min_value=0.0, value=0.15)
        fba_fee = st.number_input("FBA Fee", min_value=0.0, value=7.33)
        coupon_discount = st.number_input("Coupon Discount", min_value=0.0, value=0.05)
        cog = st.number_input("Cost of Goods", min_value=0.0, value=13.62)
        submit_daily_reports = st.form_submit_button("Submit")
    
    if submit_daily_reports:
        DailyPerformanceReportAnalyser(
            referal_fee_percentage=referal_fee_percentage,
            fba_fee=fba_fee,
            coupon_discount=coupon_discount,
            cost_of_goods=cog,
            tax=0.23,
        ).show(Reports(business_report_d, campaign_report_d))


    st.write("***")

    
    
    st.title("Performance Analysis")
    st.header("Weekly Data")
    st.write("Note: Use a 7 day period excluding the last 2 days")
    with st.form("daily-data"):
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        st.subheader("PPC Data")
        impressions = st.number_input("Impressions", min_value=0)
        clicks = st.number_input("Clicks", min_value=0)
        CPC = st.number_input("CPC", min_value=0.0)
        ppc_spend = st.number_input("Spend", min_value=0.0)
        ppc_orders = st.number_input("Orders", min_value=0)
        ppc_sales = st.number_input("Sales", min_value=0.0)

        st.subheader("Business Data")
        sessions = st.number_input("Sessions", min_value=0)
        total_orders = st.number_input("Total Orders", min_value=0)
        total_sales = st.number_input("Total Sales", min_value=0.0)

        submit = st.form_submit_button("Submit")
    
    if submit:
        date_range = DateRange(start_date=start_date, end_date=end_date)
        #if (date_range.end_date - date_range.start_date).days != 7:
        #    st.error("Date range different from 7 days")

        ppc_analysis = PPCAnalysis(
            date=date_range,
            impressions=impressions,
            clicks=clicks,
            CPC=CPC,
            ppc_spend=ppc_spend,
            ppc_orders=ppc_orders,
            ppc_sales=ppc_sales,
        )

        performance_analysis = PerformanceAnalysis(
            date=date_range,
            product=product,
            ppc_analysis=ppc_analysis,
            total_orders=total_orders,
            total_sales=total_sales,
            sessions=sessions,
            units_day_before=st.session_state["performance_data"][-1]["current_units"],
        )

        st.session_state["performance_data"].append(performance_analysis.to_dict())
        dump_performance_data(st.session_state["performance_data"], "performance_data.json")
        st.experimental_rerun()
    
    #st.write(st.session_state["performance_data"])
    st.subheader("Performance Data:")
    df_performance = pd.DataFrame(st.session_state["performance_data"])
    df_performance["Conversion Rate"] = df_performance.eval("total_orders / sessions")
    st.write(df_performance)
    #st.header("PPC KPI's")
    #fig_ppc = go.Figure()
    #fig_ppc.add_trace(
    #    go.Scatter(
    #        x=df_performance["date"],
    #        y=df_performance["impressions"],
    #        mode="lines+markers",
    #        name="Impressions"
    #    )
    #)
    #fig_ppc.add_trace(
    #    go.Scatter(
    #        x=df_performance["date"],
    #        y=df_performance["clicks"],
    #        mode="lines+markers",
    #        name="Clicks",
    #    )
    #)
    #fig_ppc.add_trace(
    #    go.Scatter(
    #       x=df_performance["date"],
    #       y=df_performance["CTR"],
    #       mode="lines+markers",
    #       name="CTR"
    #    )
    #)
    #fig_ppc.add_trace(
    #    go.Scatter(
    #       x=df_performance["date"],
    #       y=df_performance["CPC"],
    #        mode="lines+markers",
    #        name="CPC"
    #    )
    #)
    st.write("***")
    st.title("Statement Analysis")
    st.header("15-day Data")
    with st.form("statetment-data"):
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        st.subheader("PPC Data")
        impressions = st.number_input("Impressions", min_value=0)
        clicks = st.number_input("Clicks", min_value=0)
        CPC = st.number_input("CPC", min_value=0.0)
        ppc_spend = st.number_input("Spend", min_value=0.0)
        ppc_orders = st.number_input("Orders", min_value=0)
        ppc_sales = st.number_input("Sales", min_value=0.0)

        st.subheader("Business Data")
        sessions = st.number_input("Sessions", min_value=0)
        total_orders = st.number_input("Total Orders", min_value=0)
        total_sales = st.number_input("Total Sales", min_value=0.0)

        submit_statement = st.form_submit_button("Submit")
    
    if submit_statement:
        date_range = DateRange(start_date=start_date, end_date=end_date)
        #if (date_range.end_date - date_range.start_date).days != 7:
        #    st.error("Date range different from 7 days")

        ppc_analysis = PPCAnalysis(
            date=date_range,
            impressions=impressions,
            clicks=clicks,
            CPC=CPC,
            ppc_spend=ppc_spend,
            ppc_orders=ppc_orders,
            ppc_sales=ppc_sales,
        )

        performance_analysis = PerformanceAnalysis(
            date=date_range,
            product=product,
            ppc_analysis=ppc_analysis,
            total_orders=total_orders,
            total_sales=total_sales,
            sessions=sessions,
            units_day_before=st.session_state["performance_data"][-1]["current_units"],
        )

        st.write(performance_analysis.to_dict())





        

