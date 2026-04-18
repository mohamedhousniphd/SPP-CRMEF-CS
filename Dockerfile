# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Create outputs directory
RUN mkdir -p outputs

# Make port 8000 available to the world outside this container
# Railway uses the PORT environment variable
ENV PORT=8000

# Run uvicorn when the container launches
CMD uvicorn app:app --host 0.0.0.0 --port $PORT
