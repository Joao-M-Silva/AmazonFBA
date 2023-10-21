"""
Keywords Repository
Analyse the current state and evolution in time of the keywords saved in keyword tracker
"""

import streamlit as st
from keywords.classes import Keywords, KeywordsRepository
from ppc.data_readers import KeywordTrackerMergedSQP, CerebroReader
from datetime import datetime, date
import pandas as pd
from typing import List


KEYWORDS_REPOSITORY_PATH = "keywords/repository.json"
KEYWORDS_REPOSITORY_PATH_BACKUP =  "keywords/repository_backup.json"


def app():

    #if "keywords_repository" not in st.session_state:
    st.session_state["keywords_repository"] = KeywordsRepository.load(KEYWORDS_REPOSITORY_PATH)

    st.title("Tracked Keywords Analysis")
    st.header("Read Helium10 Keyword Tracker and Search Query Performance Report")
    st.write("- Note: Make sure that the reports date is aligned.")
    with st.form("files"):
        date_k = st.date_input("Date", max_value=datetime.today())
        uploader_kt = st.file_uploader("Upload Helium10 Keyword Tracker", type=[".csv"])
        # Search Query Performance Report
        uploader_sqr = st.file_uploader("Upload Monthly Search Query Performance Report", type=[".csv"])
        # Update Repository
        update_repository = st.selectbox("Update Repository?", options=[False, True])
        submit = st.form_submit_button("Submit")

    if submit:
        if not date_k:
            date_k = date.today()

        df_merged = KeywordTrackerMergedSQP(search_volume_min=1).read([uploader_kt, uploader_sqr])
        
        # Load keywords repository
        if update_repository:
            keywords_repository = KeywordsRepository.load(KEYWORDS_REPOSITORY_PATH)
            keywords_repository.save(KEYWORDS_REPOSITORY_PATH_BACKUP)
            # Convert dataframe into a class Keywords
            keywords : Keywords = Keywords.from_dataframe(
                tracking_date=date_k,
                df=df_merged,
            )
            
            # Add keywords read into the repository
            keywords_repository.add(keywords)

            st.session_state["keywords_repository"] = keywords_repository

            # Save updated repository
            keywords_repository.save(KEYWORDS_REPOSITORY_PATH)


        keyword_tracker = df_merged.query("Keyword != '-'")

        st.subheader("Left join keyword tracker and search query performance data")
        st.write("- Total number of tracked keywords: ", len(keyword_tracker))
        st.write(
            "- Number of tracked keywords without SQP data: ", 
            len(df_merged.query("`Search Query` == '-'"))
        )
        st.write(keyword_tracker)

        st.subheader("SQP search queries not yet tracked")
        sqp_data_missing = df_merged.query("Keyword == '-'").sort_values("Search Query CVR (%)", axis=0, ascending=False)
        st.write("- Total search queries: ", len(sqp_data_missing))
        columns = list(sqp_data_missing.columns)
        sqp_columns = columns[columns.index("Search Query"):]
        st.write(sqp_data_missing[sqp_columns])
        #for s in sqp_data_missing[sqp_columns]["Search Query"]:
        #    st.write(s)

        st.write("***")
        st.subheader("Candidates for Stay on Top Campaigns")
        df_stay = keyword_tracker.query("`Campaign Objective` == 'Stay on Top: Low ACOS'")
        st.write(df_stay)

        st.subheader("Candidates for Single Keyword Campaigns (SV >= 2000)")
        df_1kw = keyword_tracker.query("`Campaign Structure` == '1 KW'")
        st.write("- Total: ", len(df_1kw))
        st.write("- Total Search Volume: ", df_1kw["Search Volume"].sum())
        st.write(df_1kw)
        
        st.subheader("Candidates for 5 Keywords Campaigns (1000 <= SV < 2000)")
        df_5kw = keyword_tracker.query("`Campaign Structure` == '5 KW'")
        st.write("- Total: ", len(df_5kw))
        st.write("- Total Search Volume: ", df_5kw["Search Volume"].sum())
        st.write(df_5kw)

        st.subheader("Candidates for 10 Keywords Campaigns (250 <= SV < 1000)")
        df_10kw = keyword_tracker.query("`Campaign Structure` == '10 KW'")
        st.write("- Total: ", len(df_10kw))
        st.write("- Total Search Volume: ", df_10kw["Search Volume"].sum())
        st.write(df_10kw)

        st.subheader("Low Volume Keywords (SV < 250)")
        df_low_volume = keyword_tracker.query("`Campaign Structure` == 'All KW'")
        st.write("- Total: ", len(df_low_volume))
        st.write("- Total Search Volume: ", df_low_volume["Search Volume"].sum())
        st.write(df_low_volume)

        st.write("***")

        st.header("Ranking Analysis")
        # Keywords with no organic ranking
        st.subheader("Keywords with no organic rank")
        keywords_no_organic_rank = keyword_tracker.query("`Organic Rank` == 0")
        st.write("- Total: ", len(keywords_no_organic_rank))
        st.write("- Total Search Volume: ", keywords_no_organic_rank["Search Volume"].sum())
        st.write(keywords_no_organic_rank)
        
        # Keywords with premium organic ranking
        st.subheader("Keywords with premium organic rank")
        keywords_good_organic_rank = keyword_tracker.query("`Organic Rank` < 19 and `Organic Rank` != 0")
        st.write("- Total: ", len(keywords_good_organic_rank))
        st.write("- Total Search Volume: ", keywords_good_organic_rank["Search Volume"].sum())
        st.write(keywords_good_organic_rank)

        # Keywords with strikezone keyword ranking
        st.subheader("Keywords with strikezone keyword ranking")
        keywords_strikezone = keyword_tracker.query("`Organic Rank` >= 19 and `Organic Rank` <= 50")
        st.write("- Total: ", len(keywords_strikezone))
        st.write("- Total Search Volume: ", keywords_strikezone["Search Volume"].sum())
        st.write(keywords_strikezone)
        st.write("***")

        # Bad ranking keywords in comparision with the competitors
        st.write("**Tracked keywords with bad competitors relative rank.**")
        st.write("- Note: Keywords with more than 3 ranking competitors and relative position more than 2.")
        df_tracked_keywords_bad_rank = keyword_tracker.query("`Relative Rank Classification` == 'Bad'")
        st.write(df_tracked_keywords_bad_rank)
        st.write("- Count: ", len(df_tracked_keywords_bad_rank))
        st.write("- Total Search Volume: ", df_tracked_keywords_bad_rank["Search Volume"].sum())
        
    # Keywords Repository Analysis
    keywords_repository_analysis = st.checkbox("Keywords Repository Analysis")
    if keywords_repository_analysis:
        keywords_repository = st.session_state["keywords_repository"]
        st.title("Keywords Repository Analysis")
        st.write("- Unique Tracking Dates: ", keywords_repository.tracking_dates)
        st.plotly_chart(keywords_repository.total_search_volume_viz())
        st.plotly_chart(keywords_repository.organic_rank_classification_viz())
        st.plotly_chart(keywords_repository.search_volume_per_organic_rank_classification_viz())
        keywords_to_analyse = st.multiselect(
            "Select keywords to analyze", 
            options=keywords_repository.keyword_tracker_history()["Keyword"].unique()
        )
        if keywords_to_analyse:
            metric = st.selectbox(
                "Choose the metric to analyse", 
                options=[
                    "Search Volume",
                    "CPR",
                    "Organic Rank",
                    "Sponsored Position",
                ]
            )
            st.plotly_chart(keywords_repository.keywords_evolution_viz(keywords_to_analyse, metric))
        
        keyword_cvr = st.selectbox(
            "Select keywords for conversion rate comparison", 
            options=keywords_repository.keyword_tracker_history()["Keyword"].unique()
        )
        if keyword_cvr:
            st.plotly_chart(keywords_repository.keywords_relative_CVR_viz(keyword_cvr))

    
    st.write("***")


    st.title("Keywords Research")
    st.header("Read Helium10 Keyword Tracker and Cerebro and Search Query Performance Report")
    st.write("- Note: Make sure that the reports date is aligned.")
    with st.form("files-research"):
        uploader_kt_r = st.file_uploader("Upload Helium10 Keyword Tracker", type=[".csv"])
        uploader_cerebro_r = st.file_uploader("Upload Helium10 Cerebro", type=[".xlsx"])
        # Search Query Performance Report
        uploader_sqr_r = st.file_uploader("Upload Search Query Performance Report", type=[".csv"])
        submit_r = st.form_submit_button("Submit")

    if submit_r:
        df_merged_r = KeywordTrackerMergedSQP(search_volume_min=1).read([uploader_kt_r, uploader_sqr_r])
        df_cerebro_r = CerebroReader(search_volume_min=1).read(uploader_cerebro_r)
        
        df_r = pd.merge(
            df_cerebro_r,
            df_merged_r,
            how="left",
            left_on="Keyword Phrase",
            right_on="Keyword",
        ).sort_values("Search Volume_x", axis=0, ascending=False)

        # Filter out keywords already being tracked
        df_r["ASIN"] = df_r["ASIN"].fillna("-")
        df_r = df_r.query("ASIN == '-'")

        st.subheader("Keywords found not yet being tracked")

        # Filter columns 
        df_r = df_r[
            [
                "Keyword Phrase",
                "Search Volume_x",
                "Organic Rank_x",
                #"Sponsored Rank",
                "Search Volume Classification_x",
                "Organic Rank Classification_x",
                "Campaign Structure_x",
                "Campaign Objective_x",
                "Search Query CVR (%)",
                "ASIN CVR (%)",
                "H10 PPC Sugg. Bid",
                "H10 PPC Sugg. Min Bid",
                "H10 PPC Sugg. Max Bid",
                "CPR_x",
                

            ]
        ]

        st.write(df_r)
        
    
        #test = df_r.query("`Search Volume_x` < 250 and `Organic Rank_x` < 50 and `Organic Rank_x` != 0")
        #for _, x in test.iterrows():
        #    st.write(x["Keyword Phrase"])
            
           


    



        


