# Use official Python image as base
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy everything into the container
COPY . .

# Set the src folder in Python path so imports work
ENV PYTHONPATH=/app/src

# Create the data directory inside container
RUN mkdir -p /app/data

# Run the tracker script
CMD ["python", "src/tracker.py"]