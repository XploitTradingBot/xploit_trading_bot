from os import getenv
from dotenv import load_dotenv


def handleEnv(key:str):
    load_dotenv()
    value = getenv(key)
    if (value != None):
        return value
    raise Exception("set env file with key '{}' value".format(key))
