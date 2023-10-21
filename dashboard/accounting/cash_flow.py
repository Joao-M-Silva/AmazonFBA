from accounting.transaction import Transaction, TransactionType
import json
import pandas as pd
from typing import List, Tuple, Dict
from datetime import date
import plotly.express as px
from pathlib import Path


class NoTransactionIDFound(Exception):
    pass

class CashFlow:
    """
    Representation of the business cash flow

    Attributes:
        past_transactions_path: path for the .json file containing all
        transactions history
    """
    def __init__(self, past_transactions_path:str):
        self.path = past_transactions_path
        with open(past_transactions_path, "r") as f:
            read_transactions = [
                Transaction.__init_from_dict__(transaction_data)
                for transaction_data in json.load(f)
            ]
        
        # List with all the past transactions
        self.transactions : List[Transaction] = read_transactions

        # Create a backup file
        with open(f"{past_transactions_path}_backup.json", "w") as f:
            json.dump(self.parsable_transactions(), f)

    def __len__(self):
        return len(self.transactions)
    
    def parsable_transactions(self) -> List[Dict]:
        """
        Returns a list of parsable transactions 
        """
        return [transaction.dict() for transaction in self.transactions]
    
    def dump(self, parsable_transactions: List[Dict]):
        """
        Dump transactions
        """
        with open(self.path, "w") as f:
            json.dump(parsable_transactions, f)
    
    def add_transaction(self, transaction: Transaction) -> None:
        """
        Add a transaction to the cash flow
        """
        transaction_dict = transaction.dict()
        transaction_id = int(str(hash(frozenset(transaction_dict.items())))[:15])
        transaction.id = transaction_id
        self.transactions.append(transaction)

    def remove_transaction_by_index(self, idx: int):
        """
        Remove transaction by index
        """
        del self.transactions[idx]

    def remove_transaction_by_id(self, id: int):
        """
        Remove transaction by id
        """
        for idx, transaction in enumerate(self.transactions):
            if transaction.id == id:
                self.remove_transaction_by_index(idx)
                return None
            
        raise NoTransactionIDFound
        
    def amazon_payment(
            self, 
            amount: float,
            date: date,
            number_units_sold: int,
            cost_per_unit: int,  
            receipt: List[str],      
    ) -> None:
        """
        Definition of transaction movements once an Amazon payment is received

        Parameters:
            amount: total of money paid by Amazon 
            date: date of the Amazon payment
            number_units_sold: number of units sold associated with the Amazon payment
            cost_per_unit: cost per unit of inventory associated with the 
            Amazon payment
            receipt: receipt of the amazon payment
        """
        # Payment Transaction
        self.add_transaction(
            Transaction(
                type=TransactionType.OPERATIONS,
                date=date,
                amount=amount,
                description="Amazon payment",
                file=receipt,
            )
        )
        # Inventory Cash Flow
        cost_in_inventory = number_units_sold * cost_per_unit
        self.add_transaction(
            Transaction(
                type=TransactionType.OPERATIONS,
                date=date,
                amount=-1*cost_in_inventory,
                description="Deduct inventory costs",
            )
        )
        # Profit cash flow
        profit_to_earn = (amount - cost_in_inventory) * 0.03
        if profit_to_earn > 0.0:
            self.add_transaction(
                Transaction(
                    type=TransactionType.OPERATIONS,
                    date=date,
                    amount=-profit_to_earn,
                    description="Deduct deserved profit",
                )
            )
            self.add_transaction(
                Transaction(
                    type=TransactionType.PROFIT,
                    date=date,
                    amount=profit_to_earn,
                    description="Add deserved profit",
                )
            )

    def dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "ID":[transaction.id for transaction in self.transactions],
                "Date":[transaction.date for transaction in self.transactions],
                "Type":[transaction.type.name.capitalize() for transaction in self.transactions],
                "Description":[transaction.description for transaction in self.transactions],
                "Amount":[transaction.amount for transaction in self.transactions],
                "File":[True if transaction.file is not None else False for transaction in self.transactions],
            }
        ).sort_values("Date", ascending=False)
    
    def accrual_operating_balance(self) -> float:
        """
        Resume of the accrued operating cash flow balance. This amount represents the reserves 
        of the company to buy inventory and to do operational transactions, although the expenses
        only are stated when the amazon payment is received. This approach is best for keep
        tracking of your profit on a monthly basis
        """
        return sum(
            transaction.amount
            for transaction in self.transactions
            if transaction.type == TransactionType.OPERATIONS
        )
    
    def inventory_account_balance(self) -> float:
        """
        Balance of the money spend only for inventory purposes
        """
        return sum(
            transaction.amount 
            for transaction in self.transactions 
            if transaction.type == TransactionType.INVENTORY
        )
    
    def profit(self) -> float:
        """
        Total Profit
        """
        return sum(
            transaction.amount 
            for transaction in self.transactions 
            if transaction.type == TransactionType.PROFIT
        )
    

class Visualizer:
    def __init__(self, cash_flow:CashFlow):
        self.cash_flow = cash_flow
    
    def display_per_transaction_type(
            self, 
            transaction_type:TransactionType,
    ) -> Tuple[px.line, pd.DataFrame]:
        transaction_type_name = transaction_type.name.capitalize()
        df = self.cash_flow.dataframe().query(
                "Type == @transaction_type_name",
            ).groupby(
                "Date",
            ).sum().reset_index().sort_values("Date")
        df["CUM_AMOUNT"] = df["Amount"].cumsum()
        df["Type"] = transaction_type_name
        fig = px.line(df, x="Date", y="CUM_AMOUNT", color="Type", markers=True)
        return fig, df
            