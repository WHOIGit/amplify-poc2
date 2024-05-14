# amplify-poc2
Collection of dockerized apps for AMPLIfy PoC v2

## Overview
Images:
- Upload - Handles ingestion of new media. Saves it to S3 and emits an AMQP message which other images may be listening to
- Provenance-db - handles logging of provenance messages specifically routed to it
- Node - Multipurpse node that listens to AMQP messages, pulls data from S3, sends data to an API endpoint for processing, then emits a Provenance AMQP message + output AMQP message.


## Setup
Set Real .env parameters. copy the various env templates and fill them out with reasonable values. Make important note of the `AMQP` values to ensure that routing between images is appropriate. The cp target names are the ones expected by the docker-compose file, but ofc both names and dockerfile entries can be edited so long as they match. Some entries in the templates are present to show all the _required_ parameters, but often many of them will be already included in the Common .env file that multiple containers will use. It recommended to comment out unused/blank parameters so that they aren't parsed as BLANK/empty strings (which would otherwise overwrite the parameter if defined in the common .env).
- Common .env: `cp dotenv_temnplate .env`
- Upload .env: `cp upload/UPLOAD.env_template upload/UPLOAD.env`
- Provenance-db .env: the values required by the provenance env file technically can all be comented out as currently they are included in the common dotenv_template/`.env` file. The template exists to highlight what the required templates are 
- Node: `cp node/envs/NODE.env_template ml_anal.env` `cp node/envs/NODE.env_template dither.env`

## Usage with MinIO

Download Rancher Desktop. Do not use version 1.13.1, as it contains a Docker Compose version with a bug. Rancher Desktop 1.12.3 is confirmed to work with this project.

Next, set up MinIO for Kubernetes following [this guide](https://min.io/docs/minio/kubernetes/upstream/index.html). The instructions you'll need are:
* Download the MinIO object definition: `curl https://raw.githubusercontent.com/minio/docs/master/source/extra/examples/minio-dev.yaml -O`
* Deploy the MinIO pod: `kubectl apply -f minio-dev.yaml`
* Configure MinIO to be temporarily accessible via the browser. It will only be accessible as long as this command is running: `kubectl port-forward pod/minio 9000 9090 -n minio-dev`

Access the MinIO console at [localhost:9090](localhost:9090). The default root user credentials (username and password) are `minioadmin | minioadmin`. 

Create the neccessary buckets for your task, and enter their names into the respective environment files. For example, to perform dithering, you'll need a bucket for uploads (`UPLOAD_S3_BUCKET` in `upload/UPLOAD.env`) and a bucket for outputs (`NODE_S3_BUCKET_UPLOAD`in `node/envs/dither.env`). Ensure that the user you specific in the `.env` file has R/W access to the buckets. 

You will be able to view the bucket contents at [localhost:9090](localhost:9090).
  
## Usage
- Launch containers: `docker compose -f compose-local.yaml up --build --force-recreate -d && docker compose -f compose-local.yaml logs -f upload dither-node dither-proc provenancedb`
- Upload Content: `curl -X POST -F "file=@path/to/DyyymmddTHHMMSS_IFCBnnn.adc" http://localhost:8000/upload` `curl -X POST "http://0.0.0.0:8000/upload" -F file=@path/to/dither-candidate-image.png`
- Watch logs of various containers
- View saved Results in MongoExpress browser UI: `http://0.0.0.0:8081` 
- View saved media results in S3

