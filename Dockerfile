FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY src/ ./src/
COPY twitch_usernames.json .

# Command to run the bot
CMD ["python", "src/main.py"]