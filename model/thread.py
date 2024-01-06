#!/usr/bin/python3

from model.basemodel import BaseModel

class Thread(BaseModel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)