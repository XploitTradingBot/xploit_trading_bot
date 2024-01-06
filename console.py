#!/usr/bin/python3

import cmd
try:
    from model import storage
except Exception as e:
    print("* Connection not active *")
    print(e)
    exit(1)

from model.bot import Bot
from model.keys import Key
from model.coin import Coin
from model.user import User
from model.thread import Thread
from model.notif import Notification
from datetime import datetime
from new_listing import Executor
from model.usersession import UserSession


classes = {
    "Bot": Bot,
    "User": User,
    "Coin": Coin,
    "Notification": Notification,
    "Key": Key,
    "Executor": Executor,
    "UserSession": UserSession,
    "Thread": Thread
}

class TradingBot(cmd.Cmd):
    """This is to enable objects manipulation"""
    prompt = "(bot) "

    def do_quit(self, args):
        """This quits the console"""
        return True

    def do_all(self, args):
        """This shows a list of all objects in storage
        usage: (bot) all <class name>"""
        obj_list = []
        if not args:
            obj_dict = storage.all()
        else:
            line_arg = args.split()
            if line_arg[0] not in classes:
                print("* Class not valid *")
                return False
            else:
                obj_dict = storage.all(line_arg[0])
        for key, val in obj_dict.items():
            obj_list.append(val.to_dict())
        for item in obj_list:
            print(item)

    def do_create(self, args):
        """This create a new object and stores it in storage
        usage: (unikrib) create <class name>"""
        if not args:
            print("* Please enter a class name *")
            return False
        line_args = args.split()
        if line_args[0] not in classes:
            print("* Please enter a valid class name *")
            return False
        class_dict = {}
        for item in line_args[1:]:
            if '=' in item:
                key = item.split('=')[0]
                val = item.split('=')[1].replace('_', ' ')
                class_dict[key] = val
        
        if line_args[0] == 'User':
            if 'name' not in class_dict:
                print("* Please include user name *")
                return False
            if "email" not in class_dict:
                print("* Please include email *")
                return False
            if "password" not in class_dict:
                print("* Please include password *")
                return False
        if line_args[0] == "Coin":
            if "symbol" not in class_dict:
                print("* Please include the coin symbol *")
                return False
            for item in ["day", "month", "year", "hour", "minute", "second"]:
                if item not in class_dict:
                    print(f"* Please include the listing {item} *")
                    return False
            listing_date = datetime(int(class_dict['year']), int(class_dict['month']), int(class_dict["day"]),
                                    int(class_dict['hour']), int(class_dict['minute']), int(class_dict['second']))
            class_dict['listing_date'] = listing_date
        try:
            model = classes[line_args[0]](**class_dict)
        except Exception as e:
            print(f"* {e} *")
            return False
        print(model.id)
        model.save()

    def do_destroy(self, args):
        """This destroys an object from storage
        usage: (unikrib) destroy <class name> <class id>"""
        if not args:
            print("* Enter a class name *")
            return False
        line_args = args.split()
        if line_args[0] not in classes:
            print("* Please enter a valid class name *")
            return False
        if len(line_args) < 2:
            print("* Please enter a class id *")
            return False
        # key_search = line_args[0] + '.' + line_args[1]
        if line_args[1] == 'all':
            for obj in storage.all("Bot").values():
                obj.delete()
            return
        obj = storage.get(line_args[0], line_args[1])
        if obj is None or obj == []:
            print("* You entered an invalid instance *")
            return False
        try:
            obj.delete()
            return
        except Exception as e:
            print(e)
            self.do_quit(e)

    def do_update(self, args):
        """This updates an object in storage
        Usage: update <class name> <class id> <key> <value>"""
        if not args:
            print("* Please enter a class name *")
            return False
        line_args = args.split()
        if line_args[0] not in classes:
            print("* You entered an invalid class, please try again *")
            return False
        if len(line_args) < 2:
            print("* Please enter an id *")
            return False
        elif len(line_args) < 3:
            print("* Please enter a key *")
            return False
        elif len(line_args) < 4:
            print("* Please enter a value *")
            return False
        search_key = line_args[0] + '.' + line_args[1]
        k = line_args[2]
        if k != 'password':
            v = line_args[3].replace('_', ' ')
        else:
            v = line_args[3]
        obj = storage.get(line_args[0], line_args[1])
        if obj is None:
            print("* No instance found *")
            return False
        if v not in ('id', 'created_at', 'updated_at'):
            setattr(obj, k, v)
            obj.save()

    def do_count(self, args):
        """This prints the count of the available objects"""
        if args:
            line_args = args.split()
            if line_args[0] not in classes:
                print("* Please enter a valid class *")
                return False
            count = storage.count(line_args[0])
            print(count)
        else:
            print(storage.count())

    def do_show(self, args):
        """This prints a specific object based on cls and id
        usage: show <class name> <object id>"""
        if not args:
            print("* Please include a class name *")
            return False
        line_args = args.split()
        if line_args[0] not in classes:
            print("* Please enter a valid class name *")
            return False
        if len(line_args) < 2:
            print("* Please include an id *")
            return False
        cls = line_args[0]
        cls_id = line_args[1]
        obj = storage.get(cls, cls_id)
        if obj is None:
            print("* No instance found *")
            return False
        else:
            print(obj.to_dict())

    # def do_search(self, args):
    #     """This searches the database for an object
    #      Usage: search <classname> <a set with keyword arguments seperated by '='"""
    #     if not args:
    #         print("* Please include class name *")
    #         return False
    #     line_args = args.split()
    #     if line_args[0] not in classes:
    #         print("* Invalid class *")
    #         return False
    #     search_dict = {}
    #     for item in line_args[1:]:
    #         if "=" in item:
    #             key = item.split("=")[0]
    #             val = item.split("=")[1]
    #             search_dict[key] = val
    #     objs = storage.search(line_args[0], **search_dict)
    #     if objs is None or objs == []:
    #         print("* No {} matched *".format(line_args[0]))
    #         return False
    #     for obj in objs:
    #         print(obj.to_dict())

    def do_close(self, args):
        storage.close()


if __name__ == '__main__':
    TradingBot().cmdloop()
