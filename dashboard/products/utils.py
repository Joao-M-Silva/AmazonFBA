from dataclasses import dataclass
from enum import Enum
import math
from typing import Dict, Optional
from datetime import datetime
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go

def round_half_up(n, decimals=2):
    if isinstance(n, int) or isinstance(n, float):
        multiplier = 10 ** decimals
        return math.floor(n*multiplier + 0.5) / multiplier
    else:
        return n

class Convertions:
    @staticmethod
    def cm_to_feet(x:float) -> float:
        return x*0.032808399

    @staticmethod
    def cm_to_in(x:float) -> float:
        return x*0.3937007874

class Month(Enum):
    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12

@dataclass
class Package:
    width:float # cm
    lenght:float # cm
    height:float # cm
    weight:float # kg
    cost:float

    @property
    def dimensions(self) -> Dict[str, float]:
        return {
            "width":self.width,
            "lenght":self.lenght,
            "height":self.height,
        }

    @property
    def volume(self) -> float:
        return self.width * self.height * self.lenght

    @property
    def volume_cubic_foot(self) -> float:
        return self.volume*(Convertions.cm_to_feet(1.0)**3)
    
    def json(self) -> dict:
        """
        Into json format
        """
        return {
            "width": self.width,
            "lenght": self.lenght,
            "height": self.height,
            "weight": self.weight,
            "cost": self.cost,
        }

    def unit_storage_cost(self, month:Month) -> float:
        """
        Calculates the storage cost per unit
        """ 
        cost_per_cubic_foot = 2.4 if month.value >= 10 else 0.83
        return cost_per_cubic_foot*self.volume_cubic_foot

    def storage_cost_per_unit_sold(
        self,
        month:Month,
        initial_units_stored:int,
        average_daily_units_sold:int,
        verbose:bool=False,
    ) -> float:
        """
        Calculate the storage cost per unit sold
        """
        units_stored = []
        for day in range(31):
            current_units_stored = initial_units_stored-(average_daily_units_sold*day)
            if current_units_stored < 0:
                raise ValueError("Ran out of stock.")
            units_stored.append(current_units_stored)
        
        average_monthly_units_stored = np.array(units_stored).mean()
        
        if verbose:
            print("Average Monthly Units Stored: ", average_monthly_units_stored)
            print("Monthly Units Sold: ", average_daily_units_sold*30.5)
            print("Monthly Unit Storage Cost: ", self.unit_storage_cost(month))
            print("Number Units Left: ", current_units_stored)

        storage_cost_per_unit_sold = (
            average_monthly_units_stored * self.unit_storage_cost(month)
            / 
            (average_daily_units_sold*30.5)
        )
        if verbose:
            print("\n Storage Cost per units sold: ", storage_cost_per_unit_sold)

        return storage_cost_per_unit_sold

@dataclass
class Box:
    width:float
    lenght:float
    height:float
    weight:float
    number_packages:int
    package:Package = None

    def __post_init__(self): 
        if not all(dim < 63 for _, dim in self.dimensions.items()):
            raise ValueError("Not all dimensions are smaller than 63 cm.")
        if self.weight >= 22.6:
            raise ValueError("Box is heavier than 22.6 kg.")
        if self.package:
            if self.number_packages * self.package.weight >= self.weight:
                raise ValueError("Neglecting carton weight or bad inputs")

    @property
    def dimensions(self) -> Dict[str, float]:
        return {
            "width":self.width,
            "lenght":self.lenght,
            "height":self.height,
        }

class Fees:
    REFERAL_FEE_PERCENTAGE = 0.15
    FIXED_CLOSING_FEE = 0.99

    def __init__(self, amazon_fee:float, fulfillment_fee:float):
        self.amazon_fee = amazon_fee
        self.fulfillment_fee = fulfillment_fee
        self.total_fees = self.amazon_fee + self.fulfillment_fee

    def __repr__(self) -> str:
        return f"""
        Fees(amazon_fee={self.amazon_fee}, fulfillment_fee={self.fulfillment_fee})
        """
    
    def __str__(self) -> str:
        return f"""
        Fees(amazon_fee={self.amazon_fee}, fulfillment_fee={self.fulfillment_fee})
        """

    def json(self) -> dict:
        """
        Into json format
        """
        return {
            "amazon_fee": self.amazon_fee,
            "fulfillment_fee":self.fulfillment_fee,
        }
    
    def validate_amazon_fee(self, price:float) -> None:
        amazon_fee_calculation =round_half_up(self.REFERAL_FEE_PERCENTAGE*price + self.FIXED_CLOSING_FEE)
        if round_half_up(self.amazon_fee) == amazon_fee_calculation:
            return None
    
        raise ValueError(
            f"""
            Referal Fee Percentage or Fixed Closing Fee is outdated.
            Amazon Fee Calculation: {amazon_fee_calculation}
            """
        )
    

@dataclass
class StockFlow:
    """
    Flow of the stock:
       necessary data for an accurate profit estimation
    """
    month: Month
    initial_units_stored: int  # number of units stored in the beggining of the month
    average_daily_units_sold: int

    def json(self) -> dict:
        """
        Into json format
        """
        return {
            "month": self.month.name,
            "initial_units_stored": self.initial_units_stored,
            "average_daily_units_stored": self.average_daily_units_sold,
        }
    

@dataclass
class Product:
    name: str
    price_before_discount: float
    discount: float
    exw_cost: float
    package: Package
    shipment_cost: float
    fees: Fees
    image: str = None
    rebate_price: float = 0.6

    def __post_init__(self):
        self.price = self.price_before_discount * (1 - self.discount) - self.rebate_price
        # Total cost of goods
        self.cost = self.exw_cost + self.package.cost + self.shipment_cost
        # Amazon payment per product unit
        self.amazon_payment = self.price - self.fees.total_fees

    def json(self) -> dict:
        """
        Into json format
        """
        return {
            "name": self.name,
            "price_before_discount": self.price_before_discount,
            "discount": self.discount,
            "exw_cost": self.exw_cost,
            "package": self.package.json(),
            "shipment_cost": self.shipment_cost,
            "fees": self.fees.json(),
            "image": self.image,
        }

    def profit(
        self, 
        stock_flow: Optional[StockFlow] = None,
        TACOS: float = 0.0,
    ) -> float:
        """
        Estimate product profit
        """
        if stock_flow is None:
            return self.price - self.cost - self.fees.total_fees
        
        # Monthly storage costs
        storage_cost_per_units_sold = self.package.storage_cost_per_unit_sold(
            month=stock_flow.month,
            initial_units_stored=stock_flow.initial_units_stored,
            average_daily_units_sold=stock_flow.average_daily_units_sold,
        )

        expenses = (
            self.cost 
            + self.fees.total_fees 
            + storage_cost_per_units_sold
            + TACOS*self.price
        )

        return self.price - expenses
    
    def profit_margin(
        self, 
        stock_flow: Optional[StockFlow] = None,
        TACOS: float = 0.0,
    ) -> float:
        """
        Estimate product profit margin
        """
        return (self.profit(stock_flow=stock_flow) / self.price) - TACOS
    
    def ROI(
        self, 
        stock_flow: Optional[StockFlow] = None,
        TACOS: float = 0.0,
    ) -> float:
        """
        Estimate return on investment 
        """
        return self.profit(stock_flow=stock_flow, TACOS=TACOS) / self.cost
    
    def analysis(self, initial_number_units: int, month: Month):
        fig = make_subplots(
            rows=2, cols=1, 
            subplot_titles=("Profit Margin Analysis", "Monthly Profit Analysis"),
            shared_xaxes=True,
        )

        daily_units_sold_options = np.arange(1, 10, 1)

        for TACOS in np.arange(0.0, 0.21, 0.05):
            profit_margins = [
                self.profit_margin(
                    stock_flow=StockFlow(
                        month=month,
                        initial_units_stored=initial_number_units,
                        average_daily_units_sold=average_daily_units_sold
                    ),
                    TACOS=TACOS, 
                )
                for average_daily_units_sold in daily_units_sold_options
            ]

            fig.add_trace(
                go.Scatter(
                    x=daily_units_sold_options, 
                    y=profit_margins,
                    mode='lines+markers',
                    name=f"%TACOS = {int(TACOS*100)}",
                ),
                row=1,
                col=1,
            )

            fig.add_trace(
                go.Scatter(
                    x=daily_units_sold_options, 
                    y=[
                        profit_margin*self.price*ads*30.5 
                        for profit_margin, ads in zip(
                            profit_margins, 
                            daily_units_sold_options,
                        )
                    ],
                    mode='lines+markers',
                    name=f"%TACOS = {int(TACOS*100)}",
                ),
                row=2,
                col=1,
            )

        fig.update_xaxes(title_text="Average Daily Sales", row=2, col=1)

        fig.update_yaxes(title_text="Profit Margin", row=1, col=1)
        fig.update_yaxes(title_text="Monthly Profit", row=2, col=1)

        fig.update_layout(height=900, width=1000)
        return fig
    

