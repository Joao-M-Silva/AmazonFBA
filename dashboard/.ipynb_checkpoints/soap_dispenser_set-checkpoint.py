from dataclasses import dataclass
from enum import Enum
import math
from typing import Dict
from datetime import datetime
import numpy as np

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
    width:float
    lenght:float
    height:float
    weight:float
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
    
    def validate_amazon_fee(self, price:float) -> None:
        if round_half_up(self.amazon_fee) == round_half_up(self.REFERAL_FEE_PERCENTAGE*price + self.FIXED_CLOSING_FEE):
            return None
        raise ValueError("Referal Fee Percentage or Fixed Closing Fee is outdated")

@dataclass
class SoapDispenserSet:
    price:float
    exw_cost:float
    package:Package
    box:Box
    shipment_cost:float
    fees:Fees
    month:Month=None

    def __post_init__(self):
        self.fees.validate_amazon_fee(self.price)
        self.cost = self.exw_cost + self.package.cost + self.shipment_cost 
        if not self.month:
            for month in Month:
                if month.value == datetime.today().month:
                    self.month = month
                    print("Default Month: ", self.month.name)

    def estimate_profit_margin(
        self,
        initial_units_stored:int=1,
        average_daily_units_sold:int=1,
        percentage_on_ppc:float=0.0,
        verbose:bool=False,
    ) -> float:
        """
        Estimate the product profit margin
        """
        if percentage_on_ppc < 0 or percentage_on_ppc > 1:
            raise ValueError("Percentage of expense on PPC must be between 0 and 1")
        
        storage_cost_per_units_sold = self.package.storage_cost_per_unit_sold(
            month=self.month,
            initial_units_stored=initial_units_stored,
            average_daily_units_sold=average_daily_units_sold,
        )
        
        if verbose:
            print("Product Price: ", self.price)
            print("EXW Cost: ", self.exw_cost)
            print("Package Cost: ", self.package.cost)
            print("Shipment Cost: ", self.shipment_cost)
            print("Expense on PPC: ", percentage_on_ppc*self.price)
            print("Amazon Fee: ", self.fees.amazon_fee)
            print("Fulfillment Fee: ", self.fees.fulfillment_fee)
            
        expenses = (
            self.cost 
            +
            self.fees.total_fees
            + 
            storage_cost_per_units_sold 
            + 
            percentage_on_ppc*self.price
        )
        
        if verbose:
            print("Total Expenses: ", expenses)
        return (self.price - expenses) / self.price
    

    









