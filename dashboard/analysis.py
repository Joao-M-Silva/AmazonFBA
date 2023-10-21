from datetime import date
from dataclasses import dataclass
from enum import Enum, auto
import pandas as pd
import numpy as np
from typing import Optional, Union
from products.utils import Product


class CampaignType(Enum):
    EXACT = auto()
    PHRASE = auto()
    BROAD = auto()
    ASIN = auto()
    CATEGORY = auto()
    AUTO = auto()


@dataclass
class Campaign:
    name: str
    type_: CampaignType
    keywords: list[str]
    bid: float
    budget: float

    def __len__(self) -> int:
        return len(self.keywords)
    
    def __eq__(self, campaign):
        return campaign.name == self.name
    

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
        

@dataclass
class PPCAnalysis:
    """
    Get this data from campaign managers
    """

    date: Union[date, DateRange]
    impressions: int
    clicks: int
    CPC: float
    ppc_spend: float
    ppc_orders: int
    ppc_sales: float
    campaign: Campaign = None
    impressions_share: float = None

    
    def CTR(self):
        """
        Calculate de click-though rate
        """
        return self.clicks / self.impressions

    def CR(self):
        """
        Calculate the conversion rate
        """
        return self.ppc_orders / self.clicks

    def ACOS(self) -> Optional[float]:
        try:
            return self.ppc_spend / self.ppc_sales
        except ZeroDivisionError:
            return None
    
    def to_dict(self) -> dict:
        values = {
            "date": self.date.strftime("%Y-%m-%d"),
            "impressions": self.impressions,
            "impressions_share": self.impressions_share,
            "clicks": self.clicks,
            "CTR": self.CTR(),
            "ppc_spend": self.ppc_spend,
            "ppc_orders": self.ppc_orders,
            "ppc_sales": self.ppc_sales,
            "CPC": self.CPC,
            "CR": self.CR(),
            "ACOS": self.ACOS(),
        }  

        if self.campaign is not None:
            for k_campaign, v_campaign in self.campaign.__dict__:
                values[k_campaign] = v_campaign
        
        return values


class DailyPerformancePPC:
    """
    Analyse the PPC daily performance
    """
    def __init__(self, data: list[PPCAnalysis]):
        self.data = sorted(data, key=lambda x: x.date, reverse=False)
        assert all(x.campaign==self.data[0].campaign for x in self.data[1:])

    def resume(self) -> pd.DataFrame:
        values = {
            key: []
            for key in self.data[0].to_dict()
        }

        for d in self.data:
            for k in values:
                values[k].append(d.to_dict()[k])
        
        return pd.DataFrame(values)
                

@dataclass
class PerformanceAnalysis:
    """
    Get sales and sessions data from business reports
    """

    date: Union[date, DateRange]
    product: Product
    ppc_analysis: PPCAnalysis
    total_orders: int
    total_sales: float
    units_day_before: int
    # A session is a unique customer page visit within 24 hours
    # Even if a client visits a number of pages many times it will be
    # counted as a single session
    sessions: int
    

    def __post_init__(self):
        if self.ppc_analysis.date != self.date:
            raise Exception("Dates not equal.")

        self.estimated_amazon_fees = self.total_orders*self.product.fees.total_fees
    
    def ratio_ppc_sales(self) -> float:
        """
        Calculates the ratio of sales coming from ppc
        """
        try:
            return self.ppc_analysis.ppc_sales / self.total_sales
        except ZeroDivisionError:
            return None
    
    def ratio_ppc_clicks_sessions(self) -> float:
        """
        Calculates the ratio of sessions coming from ppc_clicks
        """
        return self.ppc_analysis.clicks / self.sessions

    def cost_per_session(self) -> float:
        """
        Calculate the ad cost per session
        """
        return self.ppc_analysis.ppc_spend / self.sessions
    
    def conversion_rate(self) -> float:
        """
        Calculate the conversion rate
        """
        return self.total_orders / self.sessions
    
    def number_sessions_per_conversion(self) -> float:
        """
        Calculate the number of sessions required to make a conversion
        """
        try:
            return 1 / self.conversion_rate()
        except ZeroDivisionError:
            return 0.0
    
    def cost_of_conversion(self) -> float:
        """
        Calculate how much it costs in ads to make a sale
        """ 
        return self.number_sessions_per_conversion() * self.cost_per_session()

    def TACOS(self) -> float:
        """
        Calculate the TACOS Ad Spent / Total Sales
        """
        try:
            return self.ppc_analysis.ppc_spend / self.total_sales
        except ZeroDivisionError:
            return None
    
    def profit_with_ppc(self) -> float:
        """
        Calculate daily profit
        """
        return (
            self.total_sales 
            - (self.total_orders*self.product.cost) 
            - self.estimated_amazon_fees
            - self.ppc_analysis.ppc_spend
        )
    
    def profit_without_ppc(self) -> float:
        """
        Calculate the daily profit without PPC
        """
        return (
            self.total_sales 
            - (self.total_orders*self.product.cost)
            - self.estimated_amazon_fees
        )
    
    def amazon_payment_with_ppc(self) -> float:
        """
        Calculate the amazon payment 
        """
        return (
            self.total_sales 
            - self.estimated_amazon_fees
            - self.ppc_analysis.ppc_spend
        )
    
    def amazon_payment_without_ppc(self) -> float:
        """
        Calculate the amazon payment without PPC
        """
        return (
            self.total_sales 
            - self.estimated_amazon_fees
        )

    def profit_per_unit_without_ppc(self) -> float:
        """
        Calculate the raw profit per unit
        """
        try:
            return self.profit_without_ppc() / self.total_orders
        except ZeroDivisionError:
            return 0.0
    
    def profit_per_unit_with_ppc(self):
        """
        Calculate the net profit per unit
        """
        return self.profit_per_unit_without_ppc() - self.cost_of_conversion()
    
    def profit_margin_with_ppc(self):
        """
        Calculate profit margin 
        """
        try:
            return self.profit_with_ppc() / self.total_sales
        except ZeroDivisionError:
            return 0.0
    
    def profit_margin_without_ppc(self):
        """
        Calculate profit margin without ppc
        """
        try:
            return self.profit_without_ppc() / self.total_sales
        except ZeroDivisionError:
            return 0.0
    
    def current_units(self):
        """
        Number of current stock
        """
        return self.units_day_before - self.total_orders
    
    def to_dict(self) -> dict:
        d = self.ppc_analysis.to_dict()
        d["total_orders"] = self.total_orders
        d["total_sales"] = self.total_sales
        d["ratio_ppc_sales"] = self.ratio_ppc_sales()
        d["sessions"] = self.sessions
        d["cost_of_conversion"] = self.cost_of_conversion()
        d["TACOS"] = self.TACOS()
        d["current_units"] = self.current_units()
        d["unit_price"] = self.product.price
        d["unit_exw_cost"] = self.product.exw_cost
        d["unit_package_cost"] = self.product.package.cost
        d["unit_shipment_cost"] = self.product.shipment_cost
        d["unit_COG"] = self.product.cost
        d["unit_fees"] = self.product.fees.total_fees
        d["unit_theoretical_profit_without_ppc"] = self.product.profit()
        d["unit_profit_without_ppc"] = self.profit_per_unit_without_ppc()
        d["unit_profit_with_ppc"] = self.profit_per_unit_with_ppc()
        d["amazon_payment_without_ppc"] = self.amazon_payment_without_ppc()
        d["amazon_payment_with_ppc"] = self.amazon_payment_with_ppc()
        d["profit_without_ppc"] = self.profit_without_ppc()
        d["profit_with_ppc"] = self.profit_with_ppc()
        d["theoretical_profit_margin"] = self.product.profit_margin()
        d["profit_margin_without_ppc"] = self.profit_margin_without_ppc()
        d["profit_margin_with_ppc"] = self.profit_margin_with_ppc()
        
        return d

    
    


    
    
    


