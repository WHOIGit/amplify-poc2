
import os
import json
from io import BytesIO
import asyncio

import httpx
import pymongo

from provenance.capture import Step
from amqp.rabbit import aio_publish
from storage.s3 import AsyncBucketStore, aiobotocore

from node_utils import AMQP_DEFAULTS, S3_DEFAULTS
from node_utils import default_amqp_logger as logger


API_ENDPOINT = os.environ['NODE_API_ENDPOINT']

AMQP_PUBLISH_ARGS = dict(
    exchange_name = os.environ['NODE_AMQP_PUBLISH_EXCHANGE_NAME'],
    exchange_type = os.getenv('NODE_AMQP_PUBLISH_EXCHANGE_TYPE','fanout'),
    routing_key   = os.getenv('NODE_AMQP_PUBLISH_ROUTINGKEY',''),
    )

def mongodb_conn_url(host, user=None, password=None, port=27017):
    auth = f"{user}:{password}@" if user and password else ""
    port = f":{port}" if port else ""
    return f"mongodb://{auth}{host}{port}"

def write_to_mongodb_from_env(entry):
    db_host = os.environ.get('NODE_OUTPUT_DB_HOST', 'localhost')
    db_user = os.environ.get('NODE_OUTPUT_DB_USER')
    db_pass = os.environ.get('NODE_OUTPUT_DB_PASSWORD')
    db_name = os.environ.get('NODE_OUTPUT_DB_NAME', 'amplify')
    db_coll = os.environ.get('NODE_OUTPUT_DB_COLLECTION', 'media2db')
    db_port = os.environ.get('NODE_OUTPUT_DB_PORT', 27017)
    db_url = mongodb_conn_url(db_host, db_user, db_pass, db_port)
    with pymongo.MongoClient(db_url) as client:
        db = client[db_name]
        collection = db[db_coll]
        inserted_id = collection.insert_one(entry).inserted_id
    return inserted_id


FILTER_KEY = os.getenv('NODE_AMQP_SUBSCRIBE_FILTER_KEY')
FILTER_VALUES = os.getenv('NODE_AMQP_SUBSCRIBE_FILTER_VALUES')
FILTER_VALUES = FILTER_VALUES.split(',') if FILTER_VALUES else None

async def callback(msg):
    if FILTER_KEY and FILTER_KEY not in msg:
        print(f'media2db: FILTER_KEY "{FILTER_KEY}" not in msg keys "{list(msg.keys())}"', flush=True)
        return
    elif FILTER_VALUES and msg[FILTER_KEY] not in FILTER_VALUES:
        print(f'media2db: FILTER_VALUES "{FILTER_VALUES}" not in msg[{FILTER_KEY}]', flush=True)
        return

    step_description = {
        'description': 'ml-analyzed.',
    }
    with Step(name='media2db', description=step_description, logger=logger) as step:
        step.add_input(name='input-bin-adc-file', description={
            'bucket': msg['bucket'],
            'key': msg['key']
        })

        # msg from upload
        # message = dict(type="upload", bucket=bucket_name, key=file.filename)
        # fetch image path in msg from s3
        s3_session = aiobotocore.session.get_session()
        async with s3_session.create_client('s3', **S3_DEFAULTS) as s3_client:
            fetched_content = await AsyncBucketStore(s3_client, msg['bucket']).get(msg['key'])
            
        # send to containerized-image-processing
        produced_content = bytearray()
        fname = os.path.basename(msg['key'])
        files = dict(adc_file=(fname,BytesIO(fetched_content)))

        async with httpx.AsyncClient().stream('POST', API_ENDPOINT, files=files,
                    follow_redirects=True, timeout=httpx.Timeout(10.0, read=None)) as resp:
            if resp.status_code == 200:
                async for chunk in resp.aiter_bytes():
                    produced_content.extend(chunk)
            else:
                error_msg = await resp.aread()
                raise ValueError(error_msg)
            
        # upload results to DB
        produced_content = produced_content.decode('utf-8')
        produced_content = json.loads(produced_content)
        db_insert_id = write_to_mongodb_from_env(produced_content)
        print(produced_content, flush=True)

        # push to amqp
        db_name = os.environ.get('NODE_OUTPUT_DB_NAME', 'amplify')
        db_coll = os.environ.get('NODE_OUTPUT_DB_COLLECTION', 'media2db')
        outgoing_msg = dict(mongo_db=db_name, mongo_collection=db_coll, inserted_id=str(db_insert_id))
        await aio_publish(outgoing_msg, **AMQP_DEFAULTS, **AMQP_PUBLISH_ARGS)
        step.add_output(name='media2db', description=outgoing_msg)
        
        
        
        
        
        
