#!/usr/bin/python3

import model
from datetime import datetime, timedelta
from model.basemodel import BaseModel


class UserSession(BaseModel):
    # __tablename__ = "usersessions"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get(self, id:str):
        sess = model.storage.get("UserSession", id)
        if not sess:
            return None
        valid_till = sess.created_at + timedelta(days=1)
        if valid_till < datetime.now():
            sess.delete()
            return None
        return sess
    
    def save(self):
        sess = model.storage.all("UserSession")
        for key, ses in sess.items():
            if ses.user_id == self.user_id:
                ses.delete()
                break
        super().save()
