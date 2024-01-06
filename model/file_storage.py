#!/usr/bin/python3

import json
# import traceback
# import new_listing
from os import getenv
from model.keys import Key
from model.bot import Bot
from model.user import User
from model.coin import Coin
# from model.thread import Thread
from model.notif import Notification
from model.usersession import UserSession

classes = {"User": User, "Notification": Notification, "Bot": Bot,
           "UserSession": UserSession, "Key": Key, "Coin": Coin}

class Storage():
    if getenv("TYPE") == "test":
        __file_path = "file.json"
    else:
        __file_path = "file.json"

    __objects = {}

    def all(self, cls=None):
        """returns the dictionary __objects"""
        if cls is not None:
            new_dict = {}
            if isinstance(cls, str):
                cls = classes[cls]
            for key, value in self.__objects.items():
                if cls == value.__class__ or cls == value.__class__.__name__:
                    new_dict[key] = value
            return new_dict
        return self.__objects

    def new(self, obj):
        """sets in __objects the obj with key <obj class name>.id"""
        if obj is not None:
            key = obj.__class__.__name__ + "." + obj.id
            self.__objects[key] = obj

    def save(self):
        """serializes __objects to the JSON file (path: __file_path)"""
        json_objects = {}
        for key in self.__objects:
            json_objects[key] = self.__objects[key].to_dict(fs=1)
        with open(self.__file_path, 'w') as f:
            json.dump(json_objects, f)

    def reload(self):
        """deserializes the JSON file to __objects"""
        try:
            with open(self.__file_path, 'r', encoding="utf-8") as f:
                jo = json.load(f)
            for key in jo:
                self.__objects[key] = classes[jo[key]["__class__"]](**jo[key])
        except FileNotFoundError:
            pass
        except Exception as e:
            print(e)

    def delete(self, obj=None):
        """delete obj from __objects if its inside"""
        if obj is not None:
            key = obj.__class__.__name__ + '.' + obj.id
            if key in self.__objects:
                del self.__objects[key]
                self.save()

    def close(self):
        """call reload() method for deserializing the JSON file to objects"""
        self.reload()

    def get(self, cls, id):
        """
        Returns the object based on the class name and its ID, or
        None if not found
        """
        if isinstance(cls, User):
            cls = "User"

        key = "{}.{}".format(cls, id)
        value = self.__objects.get(key, None)
        return value

    def count(self, cls=None):
        """
        count the number of objects in storage
        """
        return len(self.all(cls))
    
    def search(self, cls, *args, **kwargs):
        matched_obj = []
        for key, obj in self.all(cls).items():
            flag = 1
            for key, val in kwargs.items():
                if getattr(obj, key) != val:
                    flag = 0
                    break
            if flag == 1:
                matched_obj.append(obj)
            
        return matched_obj
