# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy everything into container
COPY . .

# Install Flask and dependencies
RUN pip install -r requirements.txt --no-cache-dir

# Create data directory
RUN mkdir -p /app/data

# Set Python path so imports work
ENV PYTHONPATH=/app/src

# Expose port 5000
EXPOSE 5000

# Run the Flask web app
CMD ["python", "src/app.py"]