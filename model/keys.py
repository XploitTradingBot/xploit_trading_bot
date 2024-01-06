#!/usr/bin/python3

from model.basemodel import BaseModel
import model

class Key(BaseModel):
    # __tablename__ = "keys"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "user_id" not in kwargs:
            raise ValueError("Keys must have a user_id")
        
    def save(self):
        keys = model.storage.all("Key")
        for k, key in keys.items():
            if key.user_id == self.user_id:
                new_dict = self.__dict__.copy()
                key.update(**new_dict)
                return

        super().save()
