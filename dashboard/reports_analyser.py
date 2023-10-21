import streamlit as st
from abc import ABC, abstractmethod
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from dataclasses import dataclass
from typing import Any, List
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class ReportsAnalyser(ABC):
    @abstractmethod
    def show(self, uploader):
        pass

class BusinessReportAnalyser(ReportsAnalyser):
    def read(self, uploader) -> pd.DataFrame:
        df = pd.read_csv(uploader)
        df['Date'] = pd.to_datetime(df['Date'])
        date_min = df["Date"].min().date()
        date_max = df["Date"].max().date()
        st.write("Start Date: ", date_min)
        st.write("End Date: ", date_max)
        for col in (
            "Ordered Product Sales", 
            "Average Sales per Order Item", 
            "Average Selling Price"
        ):
            df[col] = df[col].apply(
                lambda x: float(x.replace("$", "").strip())
            )
                
        df["Conversion Rate (%)"] = df.eval(
            "`Total Order Items`*100 / `Sessions - Total`"
        )

        return df
    
    def show(self, uploader):
        df = self.read(uploader)

        st.write("- Total Product Sales: ", df["Ordered Product Sales"].sum())
        st.write("- Total Units Ordered: ", df["Units Ordered"].sum())
        st.write("- Total Sessions: ", df["Sessions - Total"].sum())

        st.write(df)

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["Units Ordered"], name="Units Ordered"),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["Average Selling Price"], name="Selling Price"),
            secondary_y=True,
        )

        fig.update_layout(
            title_text="Units Ordered History"
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Date")

        # Set y-axes titles
        fig.update_yaxes(title_text="<b>primary</b> Units Ordered", secondary_y=False)
        fig.update_yaxes(title_text="<b>secondary</b> Selling Price", secondary_y=True)

        st.plotly_chart(fig)

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(
                x=df["Date"], 
                y=df["Sessions - Total"], 
                name="Total Sessions"
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=df["Date"], 
                y=df["Conversion Rate (%)"], 
                name="Conversion Rate (%)"
            ),
            secondary_y=True,
        )

        fig.update_layout(
            title_text="Conversion Rate History"
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Date")

        # Set y-axes titles
        fig.update_yaxes(title_text="<b>primary</b> Total Sessions", secondary_y=False)
        fig.update_yaxes(title_text="<b>secondary</b> Conversion Rate (%)", secondary_y=True)

        st.plotly_chart(fig)


class CampaignReportAnalyser(ReportsAnalyser):
    def __init__(self, tax: float = 0.23):
        self.tax = tax

    def read(self, uploader) -> pd.DataFrame:
        df = pd.read_csv(uploader)
        df['Date'] = pd.to_datetime(df['Date'])
        for col in (
            "Budget", 
            "Spend", 
            "7 Day Total Sales ",
        ):
            df[col] = df[col].apply(
                lambda x: float(x.replace("$", "").strip())
            )

        grouped = df.groupby("Date").sum()[
            [
                "Budget",
                "Impressions",
                "Clicks",
                "Spend",
                "7 Day Total Orders (#)",
                "7 Day Total Sales ",
            ]
        ].reset_index()

        grouped["CTR (%)"] = grouped.eval("Clicks * 100 / Impressions")
        grouped["CPC"] = grouped.eval("Spend / Clicks")
        grouped["CR (%)"] = grouped["7 Day Total Orders (#)"] * 100 / grouped["Clicks"]
        
        grouped["Spend + Tax"] = grouped["Spend"] * (1 + self.tax)
        grouped["CPC + Tax"] = grouped["CPC"] * (1 + self.tax)

        grouped["ACOS (%)"] = grouped["Spend"] * 100 / grouped["7 Day Total Sales "]
        grouped["ACOS_tax (%)"] = grouped["Spend + Tax"] * 100 / grouped["7 Day Total Sales "]

        return grouped[
            [
                "Date",
                "Budget",
                "Impressions",
                "Clicks",
                "CTR (%)",
                "Spend",
                "CPC",
                "Spend + Tax",
                "CPC + Tax",
                "7 Day Total Orders (#)",
                "CR (%)",
                "7 Day Total Sales ",
                "ACOS (%)",
                "ACOS_tax (%)"
            ]
        ]

    def show(self, uploader):
        df = self.read(uploader)
        date_min = df["Date"].min().date()
        date_max = df["Date"].max().date()
        st.write("Start Date: ", date_min)
        st.write("End Date: ", date_max)
        st.write(df)

        # Clicks Volume History
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["Impressions"], name="Impressions"),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["Clicks"], name="Clicks"),
            secondary_y=True,
        )

        fig.update_layout(
            title_text="Clicks Volume History"
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Date")

        # Set y-axes titles
        fig.update_yaxes(title_text="<b>primary</b> Units Ordered", secondary_y=False)
        fig.update_yaxes(title_text="<b>secondary</b> Selling Price", secondary_y=True)

        st.plotly_chart(fig)

        # Click-Through Rate History
        fig = make_subplots()
        fig.add_trace(
            go.Scatter(
                x=df["Date"], 
                y=df["CTR (%)"], 
                name="CTR (%)"
            ),
        )
    
        fig.update_layout(
            title_text="Click-Through Rate  History"
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Date")

        # Set y-axes titles
        fig.update_yaxes(title_text="CTR (%)")

        st.plotly_chart(fig)

        # CPC and Total Orders History
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["CPC"], name="Cost per Click"),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["7 Day Total Orders (#)"], name="7-day Total Orders"),
            secondary_y=True,
        )

        fig.update_layout(
            title_text="CPC and Total Orders History"
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Date")

        # Set y-axes titles
        fig.update_yaxes(title_text="<b>primary</b> Cost per Click", secondary_y=False)
        fig.update_yaxes(title_text="<b>secondary</b> 7-day Total Orders", secondary_y=True)

        st.plotly_chart(fig)

        # Conversion Rate History
        fig = make_subplots()
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["CR (%)"], name="Conversion Rate (%)")
        )

        fig.update_layout(
            title_text="Conversion Rate History"
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Date")

        # Set y-axes titles
        fig.update_yaxes(title_text="CR (%)")

        st.plotly_chart(fig)


        # Total Spend and Total Sales History
        fig = make_subplots()
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["Spend"], name="Spend"),
        )
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["Spend + Tax"], name="Spend + Tax"),
        )
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["7 Day Total Sales "], name="7-day Total Sales"),
        )

        fig.update_layout(
            title_text="Total Spend and Total Sales History"
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Date")

        # Set y-axes titles
        fig.update_yaxes(title_text="Total Amount")

        st.plotly_chart(fig)

        # ACOS History
        fig = make_subplots()
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["ACOS (%)"], name="ACOS without Tax"),
        )
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["ACOS_tax (%)"], name="ACOS with Tax"),
        )

        fig.update_layout(
            title_text="ACOS History"
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Date")

        # Set y-axes titles
        fig.update_yaxes(title_text="ACOS (%)")

        st.plotly_chart(fig)


@dataclass
class Reports:
    business : Any
    ppc : Any


class DailyPerformanceReportAnalyser(ReportsAnalyser):
    def __init__(
            self, 
            referal_fee_percentage: float,
            fba_fee: float,
            coupon_discount: float,
            cost_of_goods: float,
            tax: float=0.23,
        ):
        self.referal_fee_percentage = referal_fee_percentage
        self.fba_fee = fba_fee
        self.coupon_discount = coupon_discount
        self.cost_of_goods = cost_of_goods
        self.tax = tax
        
    def read(self, uploader: Reports) -> pd.DataFrame:
        df_business = BusinessReportAnalyser().read(uploader.business)
        df_ppc = CampaignReportAnalyser(tax=0.23).read(uploader.ppc)

        # Change names of ppc columns
        df_ppc = df_ppc.rename(
            columns={
                "Impressions": "PPC Impressions",
                "Clicks": "PPC Clicks",
                "CTR (%)": "PPC CTR (%)",
                "Spend": "PPC Spend",
                "Spend + Tax": "PPC Spend + Tax",
                "7 Day Total Orders (#)": "PPC Total Orders",
                "CR (%)": "PPC Conversion Rate (%)",
                "7 Day Total Sales ": "PPC Total Sales",
            }
        )

        # Merge two dataframes on date
        df_daily_performance = pd.merge(
            df_business,
            df_ppc,
            how="inner",
            on="Date",
        )

        return self.generate_features(df_daily_performance)

    def generate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df["PPC Sales / Total Sales (%)"] = (
            df["PPC Total Sales"] * 100
            /
            df["Ordered Product Sales"]
        )

        df["PPC Clicks / Sessions (%)"] = (
            df["PPC Clicks"] * 100
            /
            df["Sessions - Total"]
        )

        df["Cost per Session"] = (
            df["PPC Spend"]
            /
            df["Sessions - Total"]
        )

        df["Cost per Session + Tax"] = (
            df["PPC Spend + Tax"]
            /
            df["Sessions - Total"]
        )

        df["Number Sessions per Conversion"] = (
            1 
            / 
            (df["Conversion Rate (%)"] / 100)
        )

        df["Cost of Conversion"] = (
            df["Number Sessions per Conversion"] 
            *
            df["Cost per Session"]
        )

        df["Cost of Conversion + Tax"] = (
            df["Number Sessions per Conversion"] 
            *
            df["Cost per Session + Tax"]
        )

        df["TACOS (%)"] = (
            df["PPC Spend"] * 100
            /
            df["Ordered Product Sales"]
        )

        df["TACOS + Tax (%)"] = (
            df["PPC Spend + Tax"] * 100
            /
            df["Ordered Product Sales"]
        )

        df["Amazon Fees"] = (
            ((df["Ordered Product Sales"] * self.referal_fee_percentage) + 0.99)
            +
            (df["Units Ordered"] * self.fba_fee)
        ) 

        df["Total Sales with Coupon"] = (
            (df["Ordered Product Sales"] * (1-self.coupon_discount))
            -
            (df["Units Ordered"] * 0.6)
        )

        df["Amazon Payments"] = (
            df["Total Sales with Coupon"]
            - df["Amazon Fees"]
            - df["PPC Spend"]
        )

        df["Amazon Payments + Tax"] = (
            df["Total Sales with Coupon"]
            - df["Amazon Fees"]
            - df["PPC Spend + Tax"]
        )

        df["Profit without PPC"] = (
            df["Total Sales with Coupon"]
            - (df["Units Ordered"] * self.cost_of_goods)
            - df["Amazon Fees"]
        )

        df["Profit with PPC"] = (
            df["Total Sales with Coupon"]
            - (df["Units Ordered"] * self.cost_of_goods)
            - df["Amazon Fees"]
            - df["PPC Spend"]
        )

        df["Profit with PPC + Tax"] = (
            df["Total Sales with Coupon"]
            - (df["Units Ordered"] * self.cost_of_goods)
            - df["Amazon Fees"]
            - df["PPC Spend + Tax"]
        )

        df["Profit Margin without PPC (%)"] = (
            df["Profit without PPC"] * 100
            /
            df["Total Sales with Coupon"]
        )
        
        df["Profit Margin with PPC (%)"] = (
            df["Profit with PPC"] * 100
            /
            df["Total Sales with Coupon"]
        )

        df["Profit Margin with PPC + Tax (%)"] = (
            df["Profit with PPC + Tax"] * 100
            /
            df["Total Sales with Coupon"]
        )

        return df
    
    def display_single_y_axis(
            self, 
            df: pd.DataFrame,
            y_axis: List[str],
            y_name: List[str],
            y_title: str,
            title: str,
    ):
        fig = make_subplots()
        for  idx, y_axis in enumerate(y_axis):
            fig.add_trace(
                go.Scatter(
                    x=df["Date"],
                    y=df[y_axis],
                    name=y_name[idx],
                )
            )
        
        fig.update_layout(title_text=title)
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text=y_title)

        st.plotly_chart(fig)

    def display_double_y_axis(
            self,
            df: pd.DataFrame,
            secondary_y_axis: str,
            secondary_y_name: str,
            secondary_y_title: str,
            primary_y_axis: str,
            primary_y_name: str,
            primary_y_title: str,
            title: str
    ):
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(
                x=df["Date"], 
                y=df[primary_y_axis],
                name=primary_y_name,
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=df["Date"], 
                y=df[secondary_y_axis],
                name=secondary_y_name,
            ),
            secondary_y=True,
        )

        fig.update_layout(
            title_text=title
        )

        # Set x-axis title
        fig.update_xaxes(title_text="Date")

        # Set y-axes titles
        fig.update_yaxes(title_text=primary_y_title, secondary_y=False)
        fig.update_yaxes(title_text=secondary_y_title, secondary_y=True)

        st.plotly_chart(fig)


    def show(self, uploader: Reports):
        df = self.read(uploader)
        st.write(df)

        #Clicks and sessions
        self.display_single_y_axis(
            df,
            y_axis=["Sessions - Total", "PPC Clicks"],
            y_name=["Sessions", "PPC Clicks"],
            y_title="Total",
            title="Sessions and PPC Clicks",
        )

        self.display_double_y_axis(
            df,
            secondary_y_axis="Cost per Session",
            secondary_y_name="Cost per Session",
            secondary_y_title="Cost per Session",
            primary_y_axis="PPC Clicks / Sessions (%)",
            primary_y_name="PPC Clicks / Sessions (%)",
            primary_y_title="PPC Clicks / Sessions (%)",
            title="PPC Clicks Sessions Percentage and Cost per Session",
        )

        #Cost per Click and Cost per Session
        self.display_single_y_axis(
            df,
            y_axis=["CPC", "Cost per Session"],
            y_name=["Cost per Click", "Cost per Session"],
            y_title="Cost ($)",
            title="Cost per Click and Cost per Session",
        )

        #  Total Sales
        self.display_single_y_axis(
            df,
            y_axis=["Ordered Product Sales", "Total Sales with Coupon"],
            y_name=["Total Sales", "Total Sales with Coupon"],
            y_title="Amount ($)",
            title="Total Sales",
        )

        # Total Sales and  PPC Sales
        self.display_single_y_axis(
            df,
            y_axis=["Ordered Product Sales", "PPC Total Sales"],
            y_name=["Total Sales", "PPC Sales"],
            y_title="Amount ($)",
            title="Total Sales and PPC Sales",
        )

        self.display_single_y_axis(
            df,
            y_axis=["PPC Sales / Total Sales (%)"],
            y_name=["PPC Sales / Total Sales (%)"],
            y_title="PPC Sales / Total Sales (%)",
            title="PPC Sales Percentage",
        )

        # PPC and general conversion rates
        self.display_single_y_axis(
            df,
            y_axis=["Conversion Rate (%)", "PPC Conversion Rate (%)"],
            y_name=["Conversion Rate (%)", "PPC Conversion Rate (%)"],
            y_title="%",
            title="PPC and General Conversion Rates",
        )

        # Cost of Conversion
        self.display_single_y_axis(
            df,
            y_axis=["Cost of Conversion", "Cost of Conversion + Tax"],
            y_name=["Cost of Conversion", "Cost of Conversion + Tax"],
            y_title="Cost ($)",
            title="Cost of Conversion",
        )

        # TACOS
        self.display_single_y_axis(
            df,
            y_axis=["TACOS (%)", "TACOS + Tax (%)"],
            y_name=["TACOS (%)", "TACOS + Tax (%)"],
            y_title="TACOS (%)",
            title="TACOS",
        )

        # Amazon Payments
        self.display_single_y_axis(
            df,
            y_axis=["Amazon Payments", "Amazon Payments + Tax"],
            y_name=["Amazon Payments", "Amazon Payments + Tax"],
            y_title="Amount ($)",
            title="Amazon Payments",
        )

        # Profits
        self.display_single_y_axis(
            df,
            y_axis=["Profit without PPC", "Profit with PPC + Tax"],
            y_name=["Profit without PPC", "Profit with PPC + Tax"],
            y_title="Amount ($)",
            title="Profit",
        )

        # Profit Margins
        self.display_single_y_axis(
            df,
            y_axis=[
                "Profit Margin without PPC (%)", 
                "Profit Margin with PPC (%)",
                "Profit Margin with PPC + Tax (%)",
            ],
            y_name=[
                "Profit Margin without PPC (%)", 
                "Profit Margin with PPC (%)",
                "Profit Margin with PPC + Tax (%)",
            ],
            y_title="%",
            title="Profit Margin",
        )








