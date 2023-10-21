""" Collection of functions that read data relevant for ppc analysis"""

import pandas as pd
from datetime import date
from abc import ABC, abstractmethod
from typing import Optional, Union, List, Any


class DateRange:
    def __init__(self, start_date: date, end_date: date):
        self.start_date = start_date
        self.end_date = end_date

    def strftime(self, format: str) -> str:
        return (
            self.start_date.strftime(format) 
            + "__" 
            + self.end_date.strftime(format)
        )
    
    def __eq__(self, value) -> bool:
        return value.strftime("%Y%m%d") == self.strftime("%Y%m%d")


class DataReader(ABC):
    @abstractmethod
    def read(self, uploader: Union[Any, List[Any]]) -> pd.DataFrame:
        pass


class ActiveCampaignsReader(DataReader):
    def read(self, uploader) -> pd.DataFrame:
        df = pd.read_csv(uploader).query("State == 'ENABLED'")
        return df.sort_values("Clicks", axis=0, ascending=False)


class SearchTermReportReader(DataReader):
    def __init__(self, date_range: Optional[DateRange]=None):
        self.date_range = date_range

    def process_str(self,x: str) -> str:
        return x.lower().replace(" ","")

    def get_campaign_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        def extract(x) -> str:
            campaign_name = x["Campaign Name"]
            targeting = x["Targeting"]
            if self.process_str(targeting) in self.process_str(campaign_name):
                return "1 KW"
            elif self.process_str("5 KW") in self.process_str(campaign_name):
                return "5 KW"
            elif self.process_str("10 KW") in self.process_str(campaign_name):
                return "10 KW"
            else: return "-"
        
        df["Campaign Structure"] = df.apply(extract, axis=1)

        return df
    
    def get_campaign_objective(self, df: pd.DataFrame) -> pd.DataFrame:
        def extract(campaign_name) -> str:
            if self.process_str("Stay on Top") in self.process_str(campaign_name):
                return "Stay on Top"
            elif self.process_str("Boost") in self.process_str(campaign_name):
                return "Boost"
            elif self.process_str("Maintenance") in self.process_str(campaign_name):
                return "Maintenance"
            else: 
                return "-"
        
        df["Campaign Objective"] = df["Campaign Name"].apply(extract)

        return df
    
    def get_campaign_target_acos(self, df: pd.DataFrame) -> pd.DataFrame:
        def extract(campaign_name) -> int:
            split = self.process_str(campaign_name).split("acos")
            if len(split) == 1:
                return 0
            else:
                return int(split[1][:2])
        
        df["Campaign Target ACOS (%)"] = df["Campaign Name"].apply(extract)

        return df
    
    def read(self, uploader) -> pd.DataFrame:
        df = pd.read_excel(uploader)
        
        if self.date_range:
            if (
                (df["Start Date"].min().date() < self.date_range.start_date)
                or
                (self.date_range.end_date > df["End Date"].max().date())
            ):
                raise Exception("Selected date range and report dates doesn't match")
        
        df = df.sort_values("Clicks", axis=0, ascending=False)

        df = self.get_campaign_structure(df)

        df = self.get_campaign_objective(df)

        df = self.get_campaign_target_acos(df)

        df["Click Share (%)"] = df["Clicks"] * 100/ df["Clicks"].sum()
        df["Spend Share (%)"] = df["Spend"] * 100 / df["Spend"].sum()
        df["Sales Share (%)"] = df["7 Day Total Sales "] *100 / df["7 Day Total Sales "].sum()

        return df


class CerebroReader(DataReader):
    def __init__(self, search_volume_min: int):
        self.search_volume_min = search_volume_min

    def search_volume_classification(self, df: pd.DataFrame) -> pd.DataFrame:
        def classification(search_volume) -> str:
            if search_volume >= 2000:
                return "High"
            elif 250 <= search_volume < 2000:
                return "Decent"
            else:
                return "Poor"
            
        df["Search Volume Classification"] = df["Search Volume"].apply(classification)

        return df
    
    def organic_rank_classification(self, df: pd.DataFrame) -> pd.DataFrame:
        def classification(rank) -> str:
            if rank == 0:
                return "Inexistent"
            if rank <= 19:
                return "Premium"
            elif 19 < rank <= 50:
                return "Strikezone"
            else:
                return "Low"  
            
        df["Organic Rank Classification"] = df["Organic Rank"].apply(classification)

        return df
    
    def campaign_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        def classification(search_volume) -> str:
            if search_volume >= 2000:
                return "1 KW"
            elif 1000 <= search_volume < 2000:
                return "5 KW"
            elif 250 <= search_volume < 1000:
                return "10 KW"
            else:
                return "All KW"
            
        df["Campaign Structure"] = df["Search Volume"].apply(classification)

        return df
    
    def campaign_objective(self, df: pd.DataFrame) -> pd.DataFrame:
        def classification(x) -> str:
            if x["Campaign Structure"] in ("1 KW", "5 KW"):
                if x["Organic Rank Classification"] == "Premium":
                    return "Stay on Top: Low ACOS"
                else:
                    return "Boost: High ACOS / Maintenance: Low ACOS"
            else:
                return "Minimize ACOS"
            
        df["Campaign Objective"] = df.apply(classification, axis=1)

        return df
    
    def read(self, uploader) -> pd.DataFrame:
        df = pd.read_excel(uploader)
        df["Organic Rank"] = df["Position (Rank)"].fillna("-").apply(
            lambda x: int(x) if x != '-' else 0
        )
        search_volume_min = self.search_volume_min
        df = df.query("`Search Volume` > @search_volume_min")

        # Search volume classification
        df = self.search_volume_classification(df)

        # Organic rank classification
        df = self.organic_rank_classification(df)

        # Campaign structure
        df = self.campaign_structure(df)

        # Campaign objective
        df = self.campaign_objective(df)

        return df.sort_values("Organic Rank", axis=0, ascending=True)
    

class KeywordTrackerReader(DataReader):
    def __init__(self, search_volume_min: int):
        self.search_volume_min = search_volume_min

    def search_volume_classification(self, df: pd.DataFrame) -> pd.DataFrame:
        def classification(search_volume) -> str:
            if search_volume >= 2000:
                return "High"
            elif 250 <= search_volume < 2000:
                return "Decent"
            else:
                return "Poor"
            
        df["Search Volume Classification"] = df["Search Volume"].apply(classification)

        return df
    
    def organic_rank_classification(self, df: pd.DataFrame) -> pd.DataFrame:
        def classification(rank) -> str:
            if rank == 0:
                return "Inexistent"
            if rank <= 19:
                return "Premium"
            elif 19 < rank <= 50:
                return "Strikezone"
            else:
                return "Low"  
            
        df["Organic Rank Classification"] = df["Organic Rank"].apply(classification)

        return df
    
    def campaign_structure(self, df: pd.DataFrame) -> pd.DataFrame:
        def classification(search_volume) -> str:
            if search_volume >= 2000:
                return "1 KW"
            elif 1000 <= search_volume < 2000:
                return "5 KW"
            elif 250 <= search_volume < 1000:
                return "10 KW"
            else:
                return "All KW"
            
        df["Campaign Structure"] = df["Search Volume"].apply(classification)

        return df
    
    def campaign_objective(self, df: pd.DataFrame) -> pd.DataFrame:
        def classification(x) -> str:
            if x["Campaign Structure"] in ("1 KW", "5 KW"):
                if x["Organic Rank Classification"] == "Premium":
                    return "Stay on Top: Low ACOS"
                else:
                    return "Boost: High ACOS / Maintenance: Low ACOS"
            else:
                return "Minimize ACOS"
            
        df["Campaign Objective"] = df.apply(classification, axis=1)

        return df
    
    def competitors_relative_rank(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Classify keywords based on competitors relative rank
        """
        def classification(x) -> str:
            if (
                x["Search Volume"] > 800 
                and x["Ranking Competitors"] >= 4
                and x["Position"] >= 3
            ):
                return "Bad"
            else:
                return "Good"
            
        df["Relative Rank Classification"] = df.apply(classification, axis=1)

        return df
                
    def read(self, uploader) -> pd.DataFrame:
        def func_rank(x) -> int:
            try:
                return int(x)
            except ValueError:
                return 0

        df = pd.read_csv(uploader, index_col=False)
        df["Search Volume"] = df["Search Volume"].apply(
            lambda x: int(x) if x != '-' else 0
        )
        df["Organic Rank"] = df["Organic Rank"].apply(func_rank)
            
        df["Sponsored Position"] = df["Sponsored Position"].apply(func_rank)
        df["Position"] = df["Relative Rank"].apply(lambda x: int(x.split("/")[0]))
        df["Ranking Competitors"] = df["Ranking Asins"].apply(lambda x: int(x.split("/")[0]))
        search_volume_min = self.search_volume_min
        df = df.query("`Search Volume` > @search_volume_min")

        # Drop columns
        df = df.drop(["Ranking Asins", "Relative Rank", "Marketplace"], axis=1)

        # Search volume classification
        df = self.search_volume_classification(df)

        # Organic rank classification
        df = self.organic_rank_classification(df)

        # Campaign structure
        df = self.campaign_structure(df)

        # Campaign objective
        df = self.campaign_objective(df)

        # Relative rank classification
        df = self.competitors_relative_rank(df)

        return df.sort_values("Organic Rank", axis=0, ascending=True)
    

class SQPReader(DataReader):
    def __init__(self, keyword: str = None):
        self.keyword = keyword

    def read(self, uploader) -> pd.DataFrame:
        df = pd.read_csv(uploader, header=1).sort_values("Search Query Score", axis=0, ascending=True)
        df["Search Query CVR (%)"] = df["Purchases: Total Count"] * 100 / df["Clicks: Total Count"]
        df["ASIN CVR (%)"] = df["Purchases: ASIN Count"] * 100 / df["Clicks: ASIN Count"]
        
        if self.keyword:
            k = self.keyword
            return df.query("`Search Query` == @k")
        
        return df
    
class TopSearchReader(DataReader):
    def read(self, uploader) -> pd.DataFrame:
        df = pd.read_csv(uploader, header=1)

        return df
    
class KeywordTrackerMergedSQP(DataReader):
    def __init__(self, search_volume_min: int):
        self.search_volume_min = search_volume_min

    def read(self, uploader: list) -> pd.DataFrame:
        # Read keyword tracker and search query performance data
        keyword_tracker = KeywordTrackerReader(
            search_volume_min=self.search_volume_min,
        ).read(uploader[0])
        sqr = SQPReader().read(uploader[1])

        # Merge keyword tracker with the search query performance data
        df_merged = pd.merge(
            keyword_tracker,
            sqr,
            how="outer",
            left_on="Keyword",
            right_on="Search Query",
        ).sort_values("Search Query CVR (%)", axis=0, ascending=False)
        df_merged = df_merged.fillna("-")

        return df_merged
    

    



