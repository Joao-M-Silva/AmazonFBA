import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class PPCTrafficReport:

    """
    Analysis of the ratio of valid impressions and clicks daily
    """
    
    def __init__(self, path:str):
        self.df = pd.read_excel(path)

    def daily_analysis(self) -> pd.DataFrame:
        grouped = self.df.groupby("Date").sum()[
            [
                "Gross Impressions",
                "Impressions",
                "Invalid Impressions",
                "Gross Clicks",
                "Clicks",
                "Invalid Clicks",
            ]
        ]
        grouped["Valid Impressions Rate"] = grouped.eval("Impressions / `Gross Impressions`")
        grouped["Valid Clicks Rate"] = grouped.eval("Clicks / `Gross Clicks`")
        grouped["Valid CTR"] = grouped.eval("Clicks / Impressions")
        return grouped.reset_index()
    
    def daily_report(self):
        grouped = self.daily_analysis()
        fig = make_subplots(
            rows=5, 
            cols=1,
            subplot_titles=(
                "Impressions", 
                "Valid Impressions Rate",
                "Clicks", 
                "Valid Clicks Rate",
                "Valid CTR",
            ),
        )
        
        x = grouped["Date"]
        for name, row in (
            ("Gross Impressions", 1),
            ("Impressions", 1),
            ("Valid Impressions Rate", 2),
            ("Gross Clicks", 3),
            ("Clicks", 3),
            ("Valid Clicks Rate", 4),
            ("Valid CTR", 5),
        ):
            fig.add_trace(
                go.Scatter(
                        x=x, 
                        y=grouped[name],
                        mode='lines+markers',
                        name=name,
                ),
                row=row,
                col=1,
            )
        
        return fig
    

