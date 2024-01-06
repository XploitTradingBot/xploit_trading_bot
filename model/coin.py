#!/usr/bin/python3

from model.basemodel import BaseModel
from datetime import datetime


class Coin(BaseModel):
    # __tablename__ = "coins"
    listing_date = None
    symbol = ""
    time = "%Y-%m-%d %H:%M:%S"

    def __init__(self, *args, **kwargs):
        for item in ["listing_date", "symbol"]:
            if item not in kwargs:
                raise ValueError(f"Coin must include a {item}")
        kwargs['symbol'] = kwargs['symbol'].upper()
            
        if "/" not in kwargs['symbol']:
            raise ValueError("Inputted coin symbol is invalid, coin must end in \"USDT\"")
        
        listing_date = kwargs["listing_date"]
        if isinstance(listing_date, datetime):
            listing_date = datetime.strftime(listing_date, self.time)
        self.exchange = kwargs.get("exchange", "gate")
        
        kwargs['listing_date'] = listing_date
        kwargs.pop("day", None)
        kwargs.pop("year", None)
        kwargs.pop("month", None)
        kwargs.pop("hour", None)
        kwargs.pop("minute", None)
        kwargs.pop("second", None)
        super().__init__(*args, **kwargs)
