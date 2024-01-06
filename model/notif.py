#!/usr/bin/python3

from model.basemodel import BaseModel

class Notification(BaseModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "text" not in kwargs and "error" not in kwargs:
            raise ValueError("Notification must include a text or error")