#!/usr/bin/python3

from model.basemodel import BaseModel

class User(BaseModel):
    bot_id = None
    # subscribed_date = None

    def __init__(self, *args, **kwargs):
        self.chat_id = ""
        self.free_trial = 'unused'
        self.subscribed = False
        self.min_cap = 500
        self.txid = ""
        super().__init__(*args, **kwargs)
        
        # required_vals = ['name', 'email', 'password']
        # for item in required_vals:
        #     if item not in kwargs:
        #         raise ValueError(f"Instance must include a {item}")
