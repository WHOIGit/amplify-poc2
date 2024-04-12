import os

S3_DEFAULTS = dict(    
    endpoint_url          = os.environ['S3_HOST'],
    aws_access_key_id     = os.environ['S3_ACCESSKEY'], 
    aws_secret_access_key = os.environ['S3_PASSWORD']) 

AMQP_DEFAULTS = dict(
    host     = os.environ['AMQP_HOST'],
    user     = os.getenv('AMQP_USER','guest'),
    password = os.getenv('AMQP_PASSWORD','guest'),
)

DEFAULT_AMQP_LOGGER_ARGS = dict(
    exchange_name = os.environ['PROVENANCE_AMQP_EXCHANGE_NAME'],
    exchange_type = os.environ['PROVENANCE_AMQP_EXCHANGE_TYPE'],
    routing_key   = os.getenv('PROVENANCE_AMQP_ROUTINGKEY',''),
)

from provenance.capture import Logger
default_amqp_logger = Logger.amqp(**AMQP_DEFAULTS, **DEFAULT_AMQP_LOGGER_ARGS)

