import os

from provenance.capture import Logger, Subscriber
from couch import CouchLogger

couch_logger = CouchLogger.from_environment()
stdout_logger = Logger.stdout()

logger = Logger.fanout([couch_logger, stdout_logger])

AMQP_PARAMS = dict(
    host          = os.environ['AMQP_HOST'],
    user          = os.getenv('AMQP_USER','guest'),
    password      = os.getenv('AMQP_PASSWORD','guest'),
)

AMQP_PROVENANCE_PARAMS = dict(
    exchange_name = os.environ['PROVENANCE_AMQP_EXCHANGE_NAME'],
    exchange_type = os.getenv('PROVENANCE_AMQP_EXCHANGE_TYPE', 'fanout'),
    routing_key   = os.getenv('PROVENANCE_AMQP_ROUTINGKEY',''),
    queue_name    = os.getenv('PROVENANCE_AMQP_QUEUE',''),
)

subscriber = Subscriber(logger, **AMQP_PARAMS, **AMQP_PROVENANCE_PARAMS)

subscriber.start()
