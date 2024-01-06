#!/usr/bin/python3

from model.basemodel import BaseModel

class User(BaseModel):
    # __tablename__ = "users"
    bot_id = None
    def __init__(self, *args, **kwargs):
        self.chat_id = ""
        self.free_trial = 'unused'
        self.subscribed = False
        self.keys = {}
        self.min_cap = 0
        self.txid = None
        super().__init__(*args, **kwargs)
        
        # required_vals = ['name', 'email', 'password']
        # for item in required_vals:
        #     if item not in kwargs:
        #         raise ValueError(f"Instance must include a {item}")
