import yaml
from dataclasses import dataclass
from typing import List, Dict, Tuple


class InsuficientUnits(Exception):
    pass


@dataclass
class Unit:
    supplier:str
    name:str
    number_units:int  # number of units to produce
    exw_cost:float
    stock:int=0  # number of units left in stock after shipping
    previous_order_units:int=0  # number of units from previous order stock
    previous_order_exw_cost:float=0 # EXW cost of the previous order units
    
    @property
    def number_units_shipped(self) -> float:
        return self.number_units + self.previous_order_units - self.stock
    
    @property
    def production_cost(self) -> float:
        return self.number_units * self.exw_cost
    
    
class Product:
    def __init__(self, product:List[Tuple[Unit, int]], number_products_shipped:int):
        self.product = product
        self.number_products_shipped = number_products_shipped
        self._validate_number_products()
        
    def _validate_number_products(self):
        for unit, number_units in self.product:
            if unit.number_units_shipped < (number_units * self.number_products_shipped):
                raise InsuficientUnits("Unit %s with insuficient shipping", unit.name)
    
    @property
    def production_cost(self):
        costs = []
        for unit, number_units_per_product in self.product:
            total_units = number_units_per_product * self.number_products_shipped
            units_new = total_units - unit.previous_order_units
            cost_new = units_new * unit.exw_cost
            cost_old = (total_units - units_new) * unit.previous_order_exw_cost
            costs.append(cost_new + cost_old)
        
        return sum(costs)
    
    @property
    def EXW(self) -> float:
        """
        Unitary production cost
        """
        return self.production_cost / self.number_products_shipped
    
    def UNIT_COST(self, shipping_cost:float, assembly_cost:float, inspection_cost:float) -> float:
        """
        Unitary total cost
        """
        return (
            (self.production_cost + shipping_cost + assembly_cost + inspection_cost)
            / 
            self.number_products_shipped
        )    
        
            
        
class Order:
    
    """
    VALIDATE PREVIOUS ORDER UNITS VERSUS STOCK OF THE PREVIOUS ORDER
    """
    
    def __init__(self, order_name:str, path:str):
        with open(path, 'r') as stream:
            data_loaded = yaml.safe_load(stream)
        
        self.data = data_loaded[order_name]
    
    @property
    def suppliers(self) -> List[str]:
        return list(self.data.keys())
    
    @property
    def order_shipping_cost(self) -> float:
        return sum([content.get("shipping_cost", 0) for content in self.data.values()])
    
    @property
    def order_assembly_cost(self) -> float:
        return sum([content.get("assembly_cost", 0) for content in self.data.values()])
    
    @property
    def order_inspection_cost(self) -> float:
        return sum([content.get("inspection_cost", 0) for content in self.data.values()])
            
    @property
    def units(self) -> Dict[str, Unit]:
        units_dict = {}
        for supplier_name, content in self.data.items():
            units = content["units"]
            for unit, value in units.items():
                units_dict[unit] = Unit(supplier=supplier_name, name=unit,**value)
        
        return units_dict
    
    def supplier_production_cost(self, supplier:str) -> float:
        return sum([unit.production_cost for unit in self.units.values() if unit.supplier == supplier])
    
    @property
    def order_production_cost(self) -> float:
        return sum([self.supplier_production_cost(supplier) for supplier in self.suppliers])
        
    @property
    def order_total_cost(self) -> float:
        return (
            self.order_shipping_cost 
            + self.order_production_cost 
            + self.order_assembly_cost
            + self.order_inspection_cost
        )
    
    def product(self, definition:Dict[str, int], number_products:int) -> Product:
        """
        Input example:
        
        definition = {'tray':1, 'bottle':2}
        """
        product = []
        units = self.units
        for unit_name, number_units in definition.items():
            product.append((units[unit_name], number_units))
            
        return Product(product, number_products)
    
    def product_exw_cost(self, definition:Dict[str, int], number_products:int) -> float:
        """
        Unitary EXW Cost
        """
        product = self.product(definition, number_products)
        return product.EXW
    
    def product_unit_cost(self, definition:Dict[str, int], number_products:int) -> float:
        """
        Unitary total cost
        """
        product = self.product(definition, number_products)
        return product.UNIT_COST(
            shipping_cost=self.order_shipping_cost,
            assembly_cost=self.order_assembly_cost,
            inspection_cost=self.order_inspection_cost,
        )
            
    
            
            
        
        