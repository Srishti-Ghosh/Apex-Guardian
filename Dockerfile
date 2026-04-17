# Use an official, lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy your requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies (including the heavy data science ones)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# We don't set a CMD here because we will override it in docker-compose 
# depending on whether this container is the producer, consumer, or monitor.