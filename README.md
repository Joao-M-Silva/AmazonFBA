# AmazonFBA
Dashboard to manage amazon products.

## Introduction

Product Performance Manager (PPM) is a dashboard fully developed in Python that has the purpose of managing the full lifecycle of products selling on Amazon. The main advantage of using this dashboard is that it was developed using a modern data analysis mindset. That is, all the analysis is made by abstracting several user inputs into merged tabular Pandas dataframes followed by feature engineering. The dashboard consists of four main layers:
- PPC Optimizer: interactive workflow for PPC campaign optimization related to a specific time range. This optimization is based on the Amazon Ads Sponsored Products Search Term Report, Brand Analytics Search Query Performance Report and Helium10 Keyword Tracker.
- Performance Analysis: creates a graphical resume of the performance of the products being analyzed in a specific time frame. For example, the evolution of TACOS and the percentage of PPC sales over time. This analysis is based on the Amazon Business Report and on the Amazon Ads Sponsored Products Campaign Report. 
- Keywords Repository: a database of the time evolution of the keywords tracked for a specific product. This layer is useful to understand ranking and search volume evolution for the product keywords and, in conjunction with Helium10 Cerebro data and Brand Analytics Search Query Performance Report, there is also a section to do keyword research. 
- Accounting: responsible for managing the cash flow of the products based on accrued based accounting. That is, the product cost is only accounted for at selling time.

## Run the app
streamlit run main.py

