FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install ALL dependencies (both server and agent)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY token_server.py .
COPY voice_agent.py .
COPY main.py .

EXPOSE 10000

# Run the COMBINED server (token server + voice agent)
CMD ["python", "main.py", "start"]
