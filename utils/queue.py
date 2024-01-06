#!/usr/bin/python3

from rq import Queue
# from redis import from_url
# from utils.worker import worker
import redis
from os import getenv

redis_url = getenv('REDIS_URL')
redis_conn = redis.StrictRedis.from_url(redis_url)
# worker()

def execute_bot(executor):
    executor.start()


class Controller:
    def __init__(self):
        print("Connecting...")
        self.queue = Queue(connection=redis_conn, name='bot')
    
    def execute_bot(self, executor):
        print("Enqueuing job...")
        job = self.queue.enqueue(execute_bot(executor), executor)
        print("Job enqueued")
        return f"Job {job.id} queued"

runner = Controller()
