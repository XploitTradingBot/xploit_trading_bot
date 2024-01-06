#!/usr/bin/python3

from datetime import datetime
import model
# from model import storage
import uuid

time = "%Y-%m-%dT%H:%M:%S.%f"


class BaseModel():
    def __init__(self, *args, **kwargs):
        if kwargs:
            for key, value in kwargs.items():
                if key != "__class__":
                    setattr(self, key, value)
            if kwargs.get("created_at", None) and type(self.created_at) is str:
                self.created_at = datetime.strptime(kwargs["created_at"], time)
            else:
                self.created_at = datetime.utcnow()
            if kwargs.get("id", None) is None:
                if self.__class__.__name__ == "Key":
                    self.id = self.user_id
                else:
                    self.id = str(uuid.uuid4())
        else:
            if self.__class__.__name__ == "Key":
                self.id = self.user_id
            else:
                self.id = str(uuid.uuid4())
            self.created_at = datetime.utcnow()

    def save(self):
        model.storage.new(self)
        model.storage.save()

    def delete(self):
        model.storage.delete(self)

    def to_dict(self, fs=None):
        """returns a dictionary containing all keys/values of the instance"""
        new_dict = self.__dict__.copy()
        if "created_at" in new_dict:
            new_dict["created_at"] = new_dict["created_at"].strftime(time)
        new_dict["__class__"] = self.__class__.__name__
        if "_sa_instance_state" in new_dict:
            del new_dict["_sa_instance_state"]
        if not fs:
            if 'password' in new_dict:
                del new_dict['password']
        return new_dict
    
    def update(self, *args, **kwargs):
        try:
            for key, val in kwargs.items():
                if key == "password":
                    if self.reset_code == "Valid":
                        setattr(self, key, val)
                    else:
                        pass
                else:
                    setattr(self, key, val)
                model.storage.save()
        except Exception:
            pass