# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Install system dependencies for OpenCV and MediaPipe
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libusb-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY src/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY src/ .

# The application requires a camera and a display
# For headless environments (CI/Testing), we just run the tests
# For GUI environments, additional setup like X11 forwarding is needed

# Command to run tests by default
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]
