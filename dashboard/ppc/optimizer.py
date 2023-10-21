

import pandas as pd
from .optimization_functions import optimize_bids

class PPCOptimizer:
    def __init__(
        self, 
        df_search_term_report: pd.DataFrame,
        df_keyword_tracker_sqp: pd.DataFrame,
    ):
        
        self.columns_to_analyse = [
            "Portfolio name",
            "Campaign Structure_x",
            "Campaign Structure_y",
            "Campaign Objective_x",
            "Campaign Objective_y",
            "Targeting",
           
            "Customer Search Term",
            "Impressions", 
            "Search Volume",
            "Search Volume Classification",
            "CPR",
            "Clicks",
            "Click Share (%)",
            "Click-Thru Rate (CTR)",
            "Spend",
            "Spend Share (%)",
            "7 Day Total Units (#)",
            "7 Day Total Sales ",
            "Sales Share (%)",
            "Total Advertising Cost of Sales (ACOS) ",
            "Campaign Target ACOS (%)",
            "7 Day Conversion Rate", 
            "Search Query CVR (%)",
            "Relative Conversion Rate",
            "Organic Rank",
            "Organic Rank Classification",
            "Sponsored Position",
            "Position",
            "Relative Rank Classification",
            "Ranking Competitors",
            "Stay on Top Status",
            "Boost Status",
            "Cost Per Click (CPC)",
            "NEW BID",
            "Campaign Name",
            "Keyword",
        ]

        # Only keep the tracked keywords
        # That is, get rid of search terms on the SQP not yet being tracked
        df_keyword_tracker_sqp = df_keyword_tracker_sqp.query("ASIN != '-'")
        # Merge the search term report with the merged keyword tracker and
        # search query performance report 
        self.df = pd.merge(
            df_search_term_report,
            df_keyword_tracker_sqp,
            how="outer",
            left_on="Targeting",
            right_on="Keyword",
        ).sort_values("Clicks", axis=0, ascending=False)
        self.df = self.df.fillna("-")

        # Tracked keywords without clicks or campaigns
        self.df_no_search_term = self.df.query("`Campaign Name` == '-'")

        # Tracked keywords with clicks
        self.df_search_term = self.df.query("`Campaign Name` != '-'")
        self.df_search_term = self.relative_conversion_rate(self.df_search_term)
        self.df_search_term = self.stay_on_top_status(self.df_search_term)
        self.df_search_term = self.boost_status(self.df_search_term)

    
    def _keyword_tracker_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        columns = list(df.columns)

        return df[columns[columns.index("ASIN"):]]

    def find_premium_keywords(self, minimum_search_volume: int=1000) -> pd.DataFrame:
        """
        Find tracked keywords with premium organic rank and at least minimum search volume 
        without clicks or campaigns 
        """
        df = self.df_no_search_term.query(
            "`Organic Rank` <= 19 and `Organic Rank` != 0 and `Search Volume` >= @minimum_search_volume"
        )

        return self._keyword_tracker_columns(df)
    
    def find_strikezone_keywords(self, minimum_search_volume: int=1000) -> pd.DataFrame:
        """
        Find tracked keywords with strikezone organic rank and at least minimum search volume 
        without clicks or campaigns 
        """
        df = self.df_no_search_term.query(
            "19 < `Organic Rank` <= 50 and `Organic Rank` != 0 and `Search Volume` >= @minimum_search_volume"
        )

        return self._keyword_tracker_columns(df)
    
    def find_high_search_volume_keywords(self, minimum_search_volume: int=2000) -> pd.DataFrame:
        """
        Find tracked keywords with rank less than strikezone and
        with search volume higher than 2000 without clicks or campaigns 
        """
        df = self.df_no_search_term.query(
            "`Organic Rank` > 50 and `Search Volume` >= @minimum_search_volume"
        )

        return self._keyword_tracker_columns(df)


    def relative_conversion_rate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compare our search query conversion rate with the average
        search query conversion rate
        """
        def func(x):
            cvr = x["7 Day Conversion Rate"] * 100
            avg_cvr= x["Search Query CVR (%)"]
            try:
                if cvr >= float(avg_cvr):
                    return "Above Average"
                else:
                    return "Bellow Average"
            except:
                return "No Data"
            
        df["Relative Conversion Rate"] = df.apply(func, axis=1)

        return df
    
    
    def stay_on_top_status(self, df: pd.DataFrame) -> pd.DataFrame:
        def func(x):
            if x["Campaign Objective_x"] == "Stay on Top":
                rank = x["Organic Rank Classification"]
                if rank == "Premium":
                    return "Keep it up"
                else:
                    if x["Relative Conversion Rate"] == "Above Average":
                        return "Lost rank: Above AVG CVR"
                    elif x["Relative Conversion Rate"] == "Bellow Average":
                        return "Lost rank: Bellow AVG CVR"
                    else:
                        return "Lost rank: No CVR data"
            else:
                if x["Campaign Objective_y"] == "Stay on Top: Low ACOS":
                    return "Upgrade"
                else:
                    return "-"
        
        df["Stay on Top Status"] = df.apply(func, axis=1)

        return df
    
    def optimize_stay_on_top_campaigns(
            self,
            price: float,
            acos_target: float,
    ) -> pd.DataFrame:
        df = self.df_search_term.query("`Campaign Objective_x` == 'Stay on Top'")
        df["NEW BID"] = df.apply(
            optimize_bids,
            price=price,
            acos_target=acos_target,
            axis=1
        )

        return df[self.columns_to_analyse]

    def boost_status(self, df: pd.DataFrame) -> pd.DataFrame:
        def func(x):
            if x["Campaign Objective_x"] == "Boost":
                rank = x["Organic Rank Classification"]
                if rank == "Premium":
                    return f"Reached premium rank {rank}! Pass it to maintenance."
                else:
                    if x["Relative Conversion Rate"] == "Above Average":
                        return f"Above AVG CVR: current rank {rank}"
                    elif x["Relative Conversion Rate"] == "Bellow Average":
                        return f"Bellow AVG CVR: current rank {rank}"
                    else:
                        return f"No CVR Data: current rank {rank}"
            else:
                return "-"
    
        df["Boost Status"] = df.apply(func, axis=1)

        return df
    
    def optimize_boost_campaigns(
            self,
            price: float,
            acos_target: float,
    ) -> pd.DataFrame:
        df = self.df_search_term.query("`Campaign Objective_x` == 'Boost'")
        df["NEW BID"] = df.apply(
            optimize_bids,
            price=price,
            acos_target=acos_target,
            axis=1
        )

        return df[self.columns_to_analyse]
    
    def optimize_campaigns(
            self,
            price: float,
            acos_target: float,
    ) -> pd.DataFrame:
        df = self.df_search_term.query(
            "`Campaign Objective_x` != 'Boost'"
        ).query(
            "`Campaign Objective_x` != 'Stay on Top'"
        )
        
        df["NEW BID"] = df.apply(
            optimize_bids,
            price=price,
            acos_target=acos_target,
            axis=1
        )

        return df[self.columns_to_analyse]
    

    
    def get_new_stay_on_top_search_terms(self, df: pd.DataFrame):
        """
        Find new search terms with at least 1 click that should be 
        upgraded to stay on top campaigns
        """
        # Filter search queries not on stay o top campaigns
        df = self.df_search_term.query("`Campaign Objective_x` != 'Stay on Top'")
        df = df.query("`Organic Rank Classification` == 'Premium'")

        return df
    
    
    def stay_on_top_campaigns(self, df: pd.DataFrame):
        """
        Analysis of stay on top campaigns
        """
        # Filter search queries on stay on top campaigns
        df_stay_on_top = self.df_search_term.query("`Campaign Objective_x`  == 'Stay on Top'")
        # Create a column with the optimized bids based on ACOS target

        # Columns of interest (Organic Rank, Relative CVR, Optimized Bids)


    def boost_campaigns(self, df: pd.DataFrame):
        """
        Analysis of the performance of boost campaigns
        """
        # Filter search queries on stay on top campaigns
        df_boost = self.df_search_term.query("`Campaign Objective_x` == 'Boost'")
        # Create a column with the optimized bids based on ACOS target

        # Columns of interest (Organic Rank, Relative CVR, Optimized Bids)

        
        

    def general_campaigns(self, df: pd.DataFrame):
        """
        Analysis of non Stay on Top or Boost campagins
        """
        df = self.df_search_term.query(
            "`Campaign Objective_x` != 'Boost' and `Campaign Objective_x` != 'Stay on Top'"
        )

        # Create a column with the optimized bids based on ACOS target