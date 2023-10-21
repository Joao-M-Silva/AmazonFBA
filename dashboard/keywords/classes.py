from dataclasses import dataclass
import pandas as pd
from datetime import date
from typing import Optional, List, Union 
from enum import Enum, auto
import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

    
class SVClassification(Enum):
    HIGH = auto()
    DECENT = auto()
    POOR = auto()

class OrganicRankClassification(Enum):
    PREMIUM = auto()
    STRIKEZONE = auto()
    LOW = auto()
    INEXISTENT = auto()

class CampaignStructure(Enum):
    SingleKeyword = "1 KW"
    FiveKeywords = "5 KW"
    TenKeywords = "10 KW"
    AllKeywords = "All KW"

class CampaignObjective(Enum):
    StayOnTop = "Stay on Top: Low ACOS"
    Boost = "Boost: High ACOS"
    Maintenance = "Maintenance: Low ACOS"
    BoostOrMaintenance = "Boost: High ACOS / Maintenance: Low ACOS"
    MinimizeACOS = "Minimize ACOS"

      
@dataclass
class Keyword:
    name: str
    search_query: str
    asin: str
    tracker_search_volume: int
    sqp_search_volume: int
    cpr: int
    competing_products: str
    organic_rank: int
    average_rank: int
    sponsored_rank: int
    relative_position: int
    ranking_competitors: int
    search_volume_classification: SVClassification
    organic_rank_classification:  OrganicRankClassification
    campaign_structure: CampaignStructure
    campaign_objective: CampaignObjective
    sqp_score: int
    sqp_total_impressions: int
    sqp_asin_impressions: int
    sqp_total_clicks: int
    sqp_asin_clicks: int
    sqp_total_cart_adds: int
    sqp_asin_cart_adds: int
    sqp_total_purchases: int
    sqp_asin_purchases: int
    sqp_average_cvr: float
    sqp_asin_cvr: float

    @classmethod
    def from_row(cls, row):
        def value(x, enum: Enum):
            try:
                return enum[x.upper()]
            except KeyError:
                return x

        def value_to_member(x, enum: Enum):
            try:
                return enum._value2member_map_[x]
            except KeyError:
                return x

        values = {
            "name": row["Keyword"],
            "search_query": row["Search Query"],
            "asin": row["ASIN"],
            "tracker_search_volume": row["Search Volume"],
            "sqp_search_volume": row["Search Query Volume"],
            "cpr": row["CPR"],
            "competing_products": row["Competing Products"],
            "organic_rank": row["Organic Rank"],
            "average_rank": row["Average Rank"],
            "sponsored_rank": row["Sponsored Position"],
            "relative_position": row["Position"],
            "ranking_competitors": row["Ranking Competitors"],
            "search_volume_classification": value(
                row["Search Volume Classification"],
                SVClassification,    
            ),
            "organic_rank_classification": value(
                row["Organic Rank Classification"],
                OrganicRankClassification,  
            ),
            "campaign_structure": value_to_member(
                row["Campaign Structure"],
                CampaignStructure,
            ),
            "campaign_objective": value_to_member(
                row["Campaign Objective"],
                CampaignObjective,
            ),
            "sqp_score": row["Search Query Score"],
            "sqp_total_impressions": row["Impressions: Total Count"],
            "sqp_asin_impressions": row["Impressions: ASIN Count"],
            "sqp_total_clicks": row["Clicks: Total Count"],
            "sqp_asin_clicks": row["Clicks: ASIN Count"],
            "sqp_total_cart_adds": row["Cart Adds: Total Count"],
            "sqp_asin_cart_adds": row["Cart Adds: ASIN Count"],
            "sqp_total_purchases": row["Purchases: Total Count"],
            "sqp_asin_purchases": row["Purchases: ASIN Count"],
            "sqp_average_cvr": row["Search Query CVR (%)"],
            "sqp_asin_cvr": row["ASIN CVR (%)"],
        }

        return cls(**values)


    def into_row(self) -> dict:
        def get_enum_name(x: Union[str, Enum]) -> str:
            try:
                return x.name.capitalize()
            except AttributeError:
                return x
        
        def get_enum_value(x: Union[str, Enum]) -> str:
            try:
                return x.value
            except AttributeError:
                return x
            

        return {
            "ASIN": self.asin,
            "Keyword": self.name,
            "Search Volume": self.tracker_search_volume,
            "CPR": self.cpr,
            "Competing Products": self.competing_products,
            "Organic Rank": self.organic_rank,
            "Average Rank": self.average_rank,
            "Sponsored Position": self.sponsored_rank,
            "Position": self.relative_position,
            "Ranking Competitors": self.ranking_competitors,
            "Search Volume Classification": get_enum_name(self.search_volume_classification),
            "Organic Rank Classification": get_enum_name(self.organic_rank_classification),
            "Campaign Structure": get_enum_value(self.campaign_structure),
            "Campaign Objective": get_enum_value(self.campaign_objective),
            "Search Query": self.search_query,
            "Search Query Score": self.sqp_score,
            "Search Query Volume": self.sqp_search_volume,
            "Impressions: Total Count": self.sqp_total_impressions,
            "Impressions: ASIN Count": self.sqp_asin_impressions,
            "Clicks: Total Count": self.sqp_total_clicks,
            "Clicks: ASIN Count": self.sqp_asin_clicks,
            "Cart Adds: Total Count": self.sqp_total_cart_adds,
            "Cart Adds: ASIN Count": self.sqp_asin_cart_adds,
            "Purchases: Total Count": self.sqp_total_purchases,
            "Purchases: ASIN Count": self.sqp_asin_purchases,
            "Search Query CVR (%)": self.sqp_average_cvr,
            "ASIN CVR (%)": self.sqp_asin_cvr,
        }


class Keywords:
    def __init__(self, tracking_date: date, keywords: List[Keyword]):
        self.date = tracking_date
        self.keywords = keywords

    @classmethod
    def from_dataframe(cls, tracking_date: date, df: pd.DataFrame):
        keywords : List[Keyword] = [
            Keyword.from_row(row)
            for _, row in df.iterrows()
        ]

        return cls(
            tracking_date=tracking_date,
            keywords=keywords,
        )
    
    @classmethod
    def from_dict(cls, values: dict):
        return cls(
            tracking_date=date.fromisoformat(values["tracking_date"]),
            keywords=[
                Keyword.from_row(k) 
                for k in values["keywords"]
            ],
        )
    
    def __len__(self) -> int:
        """Number of keywords tracked"""

        return len([k for k in self.keywords if k.name != '-'])
    
    def dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                keyword.into_row()
                for keyword in self.keywords
            ]
        )
    
    def keyword_tracker(self) -> pd.DataFrame:
        df = self.dataframe()
        df = df.query("Keyword != '-'")
        df["Date"] = self.date
        df["COUNTER"] = 1
        df["Search Volume"] = df["Search Volume"].astype(int)
        df_sum = df.groupby("Date").sum().reset_index()[["Date", "COUNTER", "Search Volume"]]
        df_sum = df_sum.rename(
            columns={
                "COUNTER":"TOTAL_KEYWORDS",
                "Search Volume": "TOTAL_SEARCH_VOLUME",
            }
        )
        df = pd.merge(df, df_sum, how='inner', on="Date")

        return df
    
    def dict(self) -> dict:
        return {
            "tracking_date": self.date.isoformat(),
            "keywords": [
                keyword.into_row()
                for keyword in self.keywords
            ]
        }
    

class KeywordsRepository:
    def __init__(self, repository: List[Keywords]):
        self.repository = sorted(repository, key=lambda x: x.date)
        self.tracking_dates = [keywords.date for keywords in self.repository]

    @classmethod
    def load(cls, path: str):
        with open(path, "r") as f:
            repository_values : List[dict] = json.load(f)
        
        repository = [
            Keywords.from_dict(values)
            for values in repository_values
        ]

        return cls(repository)
    
    def __len__(self) -> int:
        return len(self.repository)
    
    def add(self, keywords: Keywords):
        if keywords.date not in self.tracking_dates:
            self.repository.append(keywords)
            self.__init__(self.repository)
        
    def serialize(self) -> List[dict]:
        return [
            k.dict()
            for k in self.repository
        ]
    
    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(self.serialize(), f)
    
    def keyword_tracker_history(self) -> pd.DataFrame:
        keyword_tracker = pd.concat(
            [rep.keyword_tracker() for rep in self.repository],
            ignore_index=True,
        )

        return keyword_tracker
    
    def total_search_volume_viz(self):
        """
        Percentage of keywords per organic rank classification
        """

        df = self.keyword_tracker_history()

        grouped = df.groupby(
            ["Date", "TOTAL_KEYWORDS", "TOTAL_SEARCH_VOLUME"]
        ).sum().reset_index()[["Date", "TOTAL_KEYWORDS", "TOTAL_SEARCH_VOLUME", "COUNTER"]]

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=grouped["Date"], 
                y=grouped["TOTAL_KEYWORDS"], 
                name="Total Keywords",
                mode="lines",
            ),
            secondary_y=False,
        )
        
        fig.add_trace(
            go.Scatter(
                x=grouped["Date"], 
                y=grouped["TOTAL_SEARCH_VOLUME"], 
                name="Total Search Volume",
                mode="lines",
            ),
            secondary_y=True,
        )

        fig.update_layout(
            title_text='Search Volume Evolution'
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Date")

        # Set y-axes titles
        fig.update_yaxes(title_text="Total Keywords", secondary_y=False)
        fig.update_yaxes(title_text="Total Search Volume", secondary_y=True)

        return fig
    
    def organic_rank_classification_viz(self):
        """
        Search volume per organic rank classification
        """

        df = self.keyword_tracker_history()

        grouped = df.groupby(
            ["Date", "TOTAL_KEYWORDS", "Organic Rank Classification"]
        ).sum().reset_index()[["Date", "Organic Rank Classification", "TOTAL_KEYWORDS", "COUNTER"]]

        grouped["Percentage Rank Classification"] = grouped.eval("COUNTER * 100 / TOTAL_KEYWORDS")

        fig = px.line(
            grouped, 
            x="Date", 
            y="Percentage Rank Classification", 
            color="Organic Rank Classification",
        )

        fig.update_layout(
            title='Organic Keyword Ranking Evolution',
            xaxis_title='Date',
            yaxis_title='%',
        )

        return fig
    
    def search_volume_per_organic_rank_classification_viz(self):
        """
        Search volume per organic rank classification
        """

        df = self.keyword_tracker_history()

        grouped = df.groupby(
            ["Date", "Organic Rank Classification"]
        ).sum().reset_index()[["Date", "Organic Rank Classification", "Search Volume"]]

        fig = px.line(
            grouped, 
            x="Date", 
            y="Search Volume", 
            color="Organic Rank Classification",
        )

        fig.update_layout(
            title='Organic Keyword Ranking Search Volume Evolution',
            xaxis_title='Date',
            yaxis_title='# Search Volume',
        )

        return fig

    def keywords_evolution_viz(self, keywords: List[str], metric: str):
        """
        Rank evolution for a set of keywords
        """
        df = self.keyword_tracker_history()
        df["INCLUDE"] = df["Keyword"].apply(lambda x: x.lower() in (k.lower() for k in keywords))
        df = df.query("INCLUDE == True")

        fig = px.line(
            df, 
            x="Date", 
            y=metric, 
            color="Keyword",
        )

        fig.update_layout(
            title=f'Keyword {metric} Evolution',
            xaxis_title='Date',
            yaxis_title=metric,
        )

        return fig
    
    def keywords_relative_CVR_viz(self, keyword: str):
        """
        Relative conversion rate
        """
        keyword = keyword.lower()
        df = self.keyword_tracker_history()
        df = df.query("Keyword == @keyword")

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["Date"], 
                y=df["Search Query CVR (%)"], 
                name="Average Conversion Rate",
                mode="lines",
            ),
        )
        
        fig.add_trace(
            go.Scatter(
                x=df["Date"], 
                y=df["ASIN CVR (%)"], 
                name="ASIN Conversion Rate",
                mode="lines",
            ),
        )

        fig.update_layout(
            title_text='Relative Conversion Rate Evolution'
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Date")

        # Set y-axes titles
        fig.update_yaxes(title_text="Conversion Rate (%)")

        return fig
    
    
    # Evolution in rank for each keyword tracked
    # Plot H10 search volume vs SQP search volume
        




    
         








    


         


