
import os
from io import BytesIO
import asyncio

import httpx

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
    

S3_UPLOAD_BUCKET = os.environ['NODE_S3_BUCKET_UPLOAD']
S3_UPLOAD_KEY_PREFIX = os.getenv('NODE_S3_UPLOAD_KEY_PREFIX','')

FILTER_KEY = os.getenv('NODE_AMQP_SUBSCRIBE_FILTER_KEY')
FILTER_VALUES = os.getenv('NODE_AMQP_SUBSCRIBE_FILTER_VALUES')
FILTER_VALUES = FILTER_VALUES.split(',') if FILTER_VALUES else None

async def callback(msg):
    if FILTER_KEY and FILTER_KEY not in msg:
        print(f'media2media: FILTER_KEY "{FILTER_KEY}" not in msg keys "{list(msg.keys())}"', flush=True)
        return
    elif FILTER_VALUES and msg[FILTER_KEY] not in FILTER_VALUES:
        print(f'media2media: FILTER_VALUES "{FILTER_VALUES}" not in msg[{FILTER_KEY}]', flush=True)
        return

    step_description = {
        'description': 'Dither an image using the Floyd-Steinberg algorithm.',
    }
    with Step(name='dither-image', description=step_description, logger=logger) as step:
        step.add_input(name='input-image', description={
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
            fetched_content = dict(file=BytesIO(fetched_content))  
            # TODO can I pass fetched_content directly to stream(..., files= _ ? 
            # See https://www.python-httpx.org/async/#streaming-requests or #streaming-responses
            async with httpx.AsyncClient().stream('POST', API_ENDPOINT, files=fetched_content, 
                        follow_redirects=True, timeout=httpx.Timeout(10.0, read=None)) as resp:
                if resp.status_code == 200:
                    async for chunk in resp.aiter_bytes():
                        produced_content.extend(chunk)
                else:
                    error_msg = await resp.aread()
                    raise ValueError(error_msg)
            
            # upload results to s3
            output_key = S3_UPLOAD_KEY_PREFIX + os.path.basename(msg["key"])
            output_key = os.path.splitext(output_key)[0]+'.png'
            await AsyncBucketStore(s3_client, S3_UPLOAD_BUCKET).put(output_key, produced_content)
        
        # push to amqp
        outgoing_msg = dict(bucket=S3_UPLOAD_BUCKET, key=output_key)
        await aio_publish(outgoing_msg, **AMQP_DEFAULTS, **AMQP_PUBLISH_ARGS)
        step.add_output(name='media2media', description=outgoing_msg)
        
        
        
        
        
        
