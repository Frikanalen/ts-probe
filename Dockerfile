# Use Python 3.10 as the base image
FROM python:3.10-slim-buster

# Install FFmpeg and other dependencies
RUN apt-get update && \
    apt-get install -y \
        ffmpeg

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script to the container
COPY ts-probe.py /app/ts-probe.py

EXPOSE 8000

# Set the entry point
ENTRYPOINT ["python", "/app/ts-probe.py"]

