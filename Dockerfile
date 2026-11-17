FROM python:3.12-slim

# Unbuffered output so logs show up straight away in the TrueNAS app logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATABASE_PATH=/data/bot.sqlite3

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files. The database is written to /data, which should be a mounted volume.
COPY src/ ./src/

# Commit and repo this image was built from, used for changelog messages.
# Set late so a new commit doesn't rebuild the layers above.
ARG GIT_SHA=""
ARG GIT_REPO=""
ENV BOT_VERSION=$GIT_SHA \
    BOT_REPO=$GIT_REPO

# Run as the TrueNAS apps user (568) rather than root
RUN mkdir -p /data && chown 568:568 /data
USER 568:568

# discord.py shuts down cleanly on SIGINT
STOPSIGNAL SIGINT

CMD ["python", "src/main.py"]
