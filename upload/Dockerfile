FROM python:3.11-slim

# Set the working directory in the container

WORKDIR /app

COPY ./requirements.txt .

# Install git, install dependencies from requirements.txt, then remove git to save space
RUN apt-get update && \
    apt-get install -y git && \
    pip install -r requirements.txt && \
    apt-get remove -y git && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the content of the local src directory to the working directory

COPY ./app/ .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
