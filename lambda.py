import os
import redis

REDIS_ENDPOINT = os.environ['REDIS_ENDPOINT']
cluster = redis.StrictRedis(host=REDIS_ENDPOINT, port=6379, db=0)

def handler(event, context):

    cluster.set('key', 'Value')

    return {
        "statusCode": 200,
        "headers": {'Content-Type': 'text/html; charset=utf-8'},
        "body": f'<p>Hello {cluster.get("key").decode()}!!!</p>'
    }
