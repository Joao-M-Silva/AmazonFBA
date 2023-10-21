"""
Optimize PPC campaigns
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
import copy
from analysis import DateRange, PPCAnalysis
from ppc import optimization_functions, data_readers
from ppc.optimizer import PPCOptimizer





def app():

    if "campaigns" not in st.session_state:
        st.session_state["campaigns"] = None

    if "search_term_report" not in st.session_state:
        st.session_state["search_term_report"] = None

    if "search_term_analysis" not in st.session_state:
        st.session_state["search_term_analysis"] = None

    if "optimizer" not in st.session_state:
        st.session_state["optimizer"] = None


    # Read advertising reports
    st.title("Read Sponsored Products Search Term Report")
    # Read advertising reports
    report = st.file_uploader("Upload Search Term Report", type=[".xlsx"])
    if report:
        st.write(data_readers.SearchTermReportReader().read(report))
        # st.write(data_readers.SearchTermReportReader().read(report)[
        #     [
        #         "Campaign Name",
        #         "Campaign Structure",
        #         "Campaign Objective",
        #         "Campaign Target ACOS (%)"
        #     ]
        # ])
    
    st.write("***")
    # Read SQP report
    st.title("Read Search Query Performance Data")
    sqp = st.file_uploader("Upload Search Query Performance Data", type=[".csv"])
    if sqp:
        df = data_readers.SQPReader().read(sqp)
        st.write(df)

    st.write("***")


    # Download the search term report
    st.title("PPC Campaigns Optimizer")
    st.header("Upload Required Data (7-day Period)")
    st.write("Important Notes:")
    st.write("1. The search term report only includes search terms with at least one click.")
    st.write("2. When creating or changing campaigns keywords, always update stars on Helium10 Keyword Tracker.")
    st.write("3. In order to check if a keyword is being used in any campaign, search the keyword on Helium10 Keyword Tracker and look if it has a star assigned.")
    with st.form("report-uploader"):
        st.warning("Exclude the last two days")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        # All the campaigns with the status available
        uploaded_active_campaigns = st.file_uploader("Upload Active Campaigns", type=[".csv"])
        # Search Term Report
        uploaded_search_term_report = st.file_uploader("Upload Search Term Report", type=[".xlsx"])
        # Search Query Performance Report
        uploaded_sqr = st.file_uploader("Upload Search Query Performance Report", type=[".csv"])
        # Helium10 keyword tracker data
        uploaded_keyword_tracker = st.file_uploader("Upload Helium10 Keyword Tracker", type=[".csv"])
        submit = st.form_submit_button("Submit")
    
    if submit:
        st.write("***")
        date_range = DateRange(start_date=start_date, end_date=end_date)
        #if (date_range.end_date - date_range.start_date).days != 7:
        #    st.error("Date range different from 7 days")

        #if (date.today() - date_range.end_date).days < 2:
        #    raise Exception("Mandatory to exclude the last 2 days")
        
        ### Active campaigns data ###
        st.session_state["campaigns"] = data_readers.ActiveCampaignsReader().read(uploaded_active_campaigns)

        ### Search term report data ###
        df_search_term_report = data_readers.SearchTermReportReader(
            date_range=date_range,
        ).read(uploaded_search_term_report)
        
        search_term_analysis = PPCAnalysis(
            date=date_range,
            impressions=int(df_search_term_report["Impressions"].sum()),
            clicks=int(df_search_term_report["Clicks"].sum()),
            CPC=df_search_term_report["Cost Per Click (CPC)"].mean(),
            ppc_spend=df_search_term_report["Spend"].sum(),
            ppc_orders=int(df_search_term_report["7 Day Total Units (#)"].sum()),
            ppc_sales=df_search_term_report["7 Day Total Sales "].sum(),
        )

        st.session_state["search_term_analysis"] = search_term_analysis
        st.session_state["search_term_report"] = df_search_term_report

        ### Search Query Performance Report ###
        df_kt_sqp = data_readers.KeywordTrackerMergedSQP(
            search_volume_min=1
        ).read([uploaded_keyword_tracker, uploaded_sqr])
        #st.session_state["keyword_tracker+search_query_performance"] = df_kt_sqp

        # Instantiate the optimizer
        optimizer = PPCOptimizer(
            df_search_term_report=df_search_term_report,
            df_keyword_tracker_sqp=df_kt_sqp,
        )

        st.session_state["optimizer"] = optimizer

    if st.session_state["optimizer"] is not None:
        st.header("Campaigns")
        st.write("- Number of active campaigns: ", len(st.session_state["campaigns"]))
        st.write(st.session_state["campaigns"])
        
        st.header("Search Term Report")
        st.write("- Targeting Reach: ", len(st.session_state["search_term_report"]))
        st.write(st.session_state["search_term_report"])
        st.write("- Analysis: ")
        st.write(st.session_state["search_term_analysis"].to_dict())

        # Find search terms that have percentage of clicks > 5%
        df_high_traffic = st.session_state["search_term_report"].query("`Click Share (%)` > 5" )
        st.write("")
        st.write("**High Traffic Search Terms**")
        st.write("- Note: Search terms with percentage of clicks higher than 5%")
        st.write(df_high_traffic)

        st.header("Helium10 Keyword Tracker")
        # Tracked keywords with clicks
        st.subheader("Tracked keywords with clicks")
        df_search_term = st.session_state["optimizer"].df_search_term
        st.write("- Count: ", len(df_search_term))
        df_search_term["Search Volume"] = df_search_term["Search Volume"].apply(lambda x: 0 if x == '-' else x)
        st.write("- Total Search Volume: ", df_search_term["Search Volume"].sum())
        # Tracked keywords without clicks or campaigns
        st.subheader("Tracked keywords without clicks or campaigns")
        df_no_search_term = st.session_state["optimizer"].df_no_search_term
        st.write("- Count: ", len(df_no_search_term))
        st.write("- Total Search Volume: ", df_no_search_term["Search Volume"].sum())
       
        st.write("***")
        
        st.title("Optimize Campaigns PPC Bids") 

        st.header("Case 1: Search Terms without clicks or campaigns")
        st.subheader("Find premium keywords (Organic Rank <= 19) with at least 1000 SV")
        st.write(st.session_state["optimizer"].find_premium_keywords(minimum_search_volume=1000))

        st.subheader("Find strikezone keywords (50 <= Organic Rank < 19) with at least 1000 SV")
        st.write(st.session_state["optimizer"].find_strikezone_keywords(minimum_search_volume=1000))
        
        st.subheader("Find high search volume keywords (Search Volume >= 2000) with poor organic ranking.")
        st.write(st.session_state["optimizer"].find_high_search_volume_keywords(minimum_search_volume=2000))
        
        st.header("Case 2: Search Terms with clicks")
        acos_target = st.number_input("Target ACOS", value=0.3, min_value=0.0, max_value=0.8)
        current_price = st.number_input("Current Price", value=39.99, min_value=24.99)
        discount = st.number_input("Discount", min_value=0.0, max_value=0.5, value=0.05)
        price = current_price * (1 - discount)
        
        st.subheader("Optimize Stay on Top campaigns")
        st.write(
            st.session_state["optimizer"].optimize_stay_on_top_campaigns(
                price=price, 
                acos_target=acos_target
            )
        )

        st.subheader("Optimize Boost campaigns")
        try:
            st.write(
                st.session_state["optimizer"].optimize_boost_campaigns(
                    price=price, 
                    acos_target=acos_target
                )
            )
        except ValueError:
            st.warning("No Boost campaigns with clicks.")

        st.subheader("Optimize the rest of the campaigns")
        st.write(
            st.session_state["optimizer"].optimize_campaigns(
                price=price, 
                acos_target=acos_target
            )
        )
        


        # ANALYSE BOOST CAMPAIGNS AND DO BID ADJUSTMENT

        # ANALYSE REST OF CAMPAIGNS AND DO BID ADJUSTMENT


        

        # target_acos = st.number_input("Target ACOS", value=0.3, min_value=0.0, max_value=0.8)
        # current_price = st.number_input("Current Price", value=39.99, min_value=24.99)
        # discount = st.number_input("Discount", min_value=0.0, max_value=0.5)
        # st.subheader("Steps for exact campaigns:")
        # st.write(
        #     """
        #     - Step 1: Any Search Term with 0 sales and 
        #     number_clicks > (1,2.ACOS_target.price / CPC) - 1 
        #     set bid to 
        #     ACOS_target.price / (1 + number_clicks). 
        #     Unless it is a search term that dominates the number of clicks. 
        #     """
        # )
        # st.write(
        #     """
        #     - Step 2: ny Search Term with 0 sales and 
        #     number_clicks < (ACOS_target.0,75.price / CPC) - 1, use:
        #     new_CPC = CPC.1,1
        #     """
        # )
        # st.write(
        #     """
        #     - Step 3: Any keyword or product traget with an ACOS < ACOS_target, use:
        #     new_CPC = CPC.1,2
        #     """
        # )
        # st.write(
        #     """
        #     - Step 4: Any keyword or product traget with an ACOS > ACOS_target, use:
        #     new_CPC = (ACOS_target / ACOS).CPC
        #     """
        # )

        # st.subheader("Steps for broad and phrase campaigns:")
        # st.write(
        #     """
        #     - Step 1: Any Search Term with 0 sales and 
        #     number_clicks > (1,2.ACOS_target.price / CPC) - 1 
        #     set bid to 
        #     ACOS_target.price / (1 + number_clicks). 
        #     Unless it is a search term that dominates the number of clicks. 
        #     """
        # )
        
        # optimize = st.button("Optimize")
        # if optimize:
        #     st.write("- Deal with campaigns with low impressions and zero clicks")
        #     df_optimize = copy.deepcopy(st.session_state["search_term_report"])
        #     df_optimize["NEW_BID"] = df_optimize.apply(
        #         optimization_functions.optimize_bids,
        #         ACOS_target=target_acos,
        #         price=current_price * (1 - discount),
        #         high_traffic_search_terms=high_traffic_search_terms,
        #         keywords_bad_ranking=keywords_bad_ranking,
        #         keywords_good_ranking=keywords_good_ranking,
        #         axis=1,
        #     )
        #     df_optimize["OLD_BID"] = df_optimize["Cost Per Click (CPC)"]
        #     st.subheader("Optimized Bids")
        #     st.write(df_optimize)
        #     st.write(df_optimize[
        #             [
        #                 "Campaign Name", 
        #                 "Targeting", 
        #                 "Customer Search Term", 
        #                 "Click Share (%)",
        #                 "Spend Share (%)",
        #                 "Sales Share (%)"
        #                 "NEW_BID", 
        #                 "OLD_BID",
        #                 "7 Day Total Orders (#)",
        #             ]
        #         ]
        #     )
            
        #     st.write("**- Note: Increase bids for search terms without clicks**")
            
        

        
        
        

        