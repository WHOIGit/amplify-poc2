import os

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

from amqp.rabbit import aio_publish
from storage.s3 import AsyncBucketStore, aiobotocore


S3_CLIENT_ARGS = dict(
    endpoint_url          = os.environ['S3_HOST'],
    aws_access_key_id     = os.environ['S3_ACCESSKEY'],
    aws_secret_access_key = os.environ['S3_PASSWORD'],
)

UPLOAD_BUCKET = os.environ['UPLOAD_S3_BUCKET']
S3_KEY_PREFIX = os.getenv('UPLOAD_S3_KEY_PREFIX','')

AMQP_PUBLISH_ARGS = dict(
    host          = os.environ['AMQP_HOST'],
    user          = os.getenv('AMQP_USER','guest'),
    password      = os.getenv('AMQP_PASSWORD','guest'),
    exchange_name = os.environ['UPLOAD_AMQP_PUBLISH_EXCHANGE_NAME'],
    exchange_type = os.getenv('UPLOAD_AMQP_PUBLISH_EXCHANGE_TYPE','fanout'),
    routing_key   = os.getenv('UPLOAD_AMQP_PUBLISH_ROUTINGKEY',''),
)
print(AMQP_PUBLISH_ARGS)

app = FastAPI()


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read the file contents
        file_contents = await file.read()
        storage_filename = S3_KEY_PREFIX + file.filename

        # Upload the file to S3
        s3_session = aiobotocore.session.get_session()
        async with s3_session.create_client('s3', **S3_CLIENT_ARGS) as s3_client:
            await AsyncBucketStore(s3_client, UPLOAD_BUCKET).put(storage_filename, file_contents)

        # Publish a message to the exchange
        message = {
            "type": "upload",
            "bucket": UPLOAD_BUCKET,
            "key": storage_filename,
            "ext": os.path.splitext(file.filename)[1]
        }

        await aio_publish(message, **AMQP_PUBLISH_ARGS)

        return JSONResponse(content={"message": "File uploaded successfully"}, status_code=200)
    except Exception as e:
        print(e)
        return JSONResponse(content={"error": str(e)}, status_code=500)
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

