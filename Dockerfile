FROM python:3-slim-bookworm

# Install FFmpeg and other dependencies
RUN apt-get update && \
    apt-get install -y \
    ffmpeg

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script to the container
COPY *.py /app/

EXPOSE 8000

# Set the entry point
ENTRYPOINT ["python", "/app/ts_probe.py"]

