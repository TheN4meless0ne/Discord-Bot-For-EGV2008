FROM python:3.12-slim

# Unbuffered output so logs show up straight away in the TrueNAS app logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TWITCH_USERNAMES_FILE=/data/twitch_usernames.json \
    DEFAULT_TWITCH_USERNAMES_FILE=/app/twitch_usernames.json

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files. The bundled usernames list is only a seed: the live list
# is written to /data, which should be a mounted volume.
COPY src/ ./src/
COPY twitch_usernames.json .

# Run as the TrueNAS apps user (568) rather than root
RUN mkdir -p /data && chown 568:568 /data
USER 568:568

CMD ["python", "src/main.py"]
