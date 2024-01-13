#!/usr/bin/python3

import json
from model.user import User
from typing import List

classes = {"User": User}


class Storage():
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

    def recreate(self, objs:List):
        """This recreates all the objects in the argument into storage"""
        for obj in objs:
            key = f"{obj['__class__']}.{obj['id']}"
            if key in self.__objects:
                model = self.__objects[key]
                for attr in ['alerted', 'trial_alerted']:
                    if hasattr(model, attr):
                        obj[attr] = getattr(model, attr)
            # print("Setting new user")

            self.__objects[key] = classes[obj['__class__']](**obj)
        self.save()

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
