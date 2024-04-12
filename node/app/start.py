import os
import asyncio
from importlib import import_module
from amqp.rabbit import aio_subscribe


AMQP_SUBSCRIPTION = dict(
    host          = os.environ['AMQP_HOST'],
    user          = os.getenv('AMQP_USER','guest'),
    password      = os.getenv('AMQP_PASSWORD','guest'),
    exchange_name = os.environ['NODE_AMQP_SUBSCRIBE_EXCHANGE_NAME'],
    exchange_type = os.getenv('NODE_AMQP_SUBSCRIBE_EXCHANGE_TYPE','fanout'),
    routing_key   = os.getenv('NODE_AMQP_SUBSCRIBE_ROUTINGKEY',''),
    queue_name    = os.getenv('NODE_AMQP_SUBSCRIBE_QUEUE',''),
    qos           = int(os.getenv('NODE_AMQP_SUBSCRIBE_QOS') or 1),
)

callback_module = import_module( 'callbacks.' + os.environ['NODE_CALLBACK_MODULE'] )
callback_func = os.getenv('NODE_CALLBACK_FUNC','callback')
callback_func = getattr(callback_module, callback_func)

print(AMQP_SUBSCRIPTION)


# LISTENS TO subscribe_to AND RUNS callback for each incomming message
asyncio.run( aio_subscribe(callback_func, **AMQP_SUBSCRIPTION) )


