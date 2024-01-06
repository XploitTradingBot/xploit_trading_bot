#!/usr/bin/python3
from model.basemodel import BaseModel
# import model

class Bot(BaseModel):
    # __tablename__ = "bots"
    executor_id = ""
    capital = 100
    exchange = None
    stopFlag =  False

    def __init__(self, *args, **kwargs):
        if "user_id" not in kwargs:
            raise ValueError("Bot must have a user_id")
        
        # self.transactions = []
        self.read_logs = []
        self.unread_logs = []
        self.active = True
        super().__init__(*args, **kwargs)

    def save(self):
        from model import storage
        all_bots = storage.search("Bot", user_id=self.user_id)
        for bot in all_bots:
            if bot.id != self.id:
                print(f"Deleting bot with id: {bot.id}")
                bot.delete()

        super().save()
