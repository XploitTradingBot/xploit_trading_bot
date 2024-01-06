#!/usr/bin/python3

from redis import Redis
from rq import Worker, Queue
# from os import getenv


def worker():
    # Connect to the Redis server
    # redis_url = getenv("REDIS_URL")
    redis_conn = Redis()

    # Create a queue
    queue = Queue(connection=redis_conn)

    # Create a worker and process jobs from the default queue
    worker = Worker([queue], connection=redis_conn)
    worker.work()
    print("Worker process started")

