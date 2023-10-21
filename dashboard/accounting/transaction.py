from enum import Enum, auto
from datetime import date, datetime
from dataclasses import dataclass
from typing import List
import base64
import io
import PIL


class TransactionType(Enum):
    """
    Different types of transactions
    """
    OPERATIONS = auto()
    INVENTORY = auto()
    TAX = auto()
    PROFIT = auto()


@dataclass
class Transaction:
    """
    Definition of a transaction
    """
    type: TransactionType
    date: date
    amount: float
    description: str
    # List of files associated with the
    # transaction in base64
    file: List[str] = None
    id: int = None

    @classmethod
    def __init_from_dict__(cls, data: dict):
        file_ = data.get("file", None)
        return cls(
            type=TransactionType[data["type"]],
            date=datetime.strptime(data["date"], "%Y-%m-%d").date(),
            amount=data["amount"],
            description=data["description"],
            file=list(file_) if file_ is not None else None,
            id=data.get("id", None),
        )

    def __post_init__(self):
        if self.date > date.today():
            raise ValueError("Transaction date is in the future.")
        
    def file_images(self):
        """
        Get a list of PIL images for the file
        """
        images = []
        for x in self.file:
            image = PIL.Image.open(io.BytesIO(base64.b64decode(x)))
            images.append(image)
        
        return images

    def dict(self) -> dict:
        """
        Return a parsable dictionary
        """
        return {
            "type":self.type.name,
            "date":str(self.date),
            "amount":self.amount,
            "description":self.description,
            "file":tuple(self.file) if self.file is not None else None,
            "id":self.id,
        }


    
    

    