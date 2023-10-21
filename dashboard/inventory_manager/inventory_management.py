from datetime import datetime, timedelta

class InventoryManager:
    def __init__(
        self, 
        lead_time:int,  #Production + Shipping
        current_stock:int,
   ) -> None:
        #Last update date
        self.last_update_date = datetime.today()
        #Lead Time
        self.lead_time = lead_time + 5
        #Current Stock
        self.current_stock = current_stock

    def days_worth_inventory(self, daily_sales:int) -> float:
        return self.current_stock / daily_sales

    def reorder_info(self, daily_sales:int) -> int:
        days_worth_inventory = self.days_worth_inventory(daily_sales)
        #Number of days till reorder
        reorder_days = days_worth_inventory - self.lead_time
        reorder_date = datetime.today() + timedelta(days=round(reorder_days))
        print("Number of days till next reorder: ", round(reorder_days))
        print("Date to reorder: ", reorder_date)
        
        return round(reorder_days)

    
    


    