# Use the official Python 3.10 image with Ubuntu
FROM nvidia/cuda:11.6.2-base-ubuntu20.04

LABEL author="janle"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV CMAKE_ARGS="-DLLAMA_CUBLAS=on"

# Update and upgrade packages
#RUN apt update && apt upgrade -y

# Install Python

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3.10 \
        python3-pip \
        gcc \
        git \
        g++ \
        && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file separately to leverage Docker cache
COPY server/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
#RUN pip install --no-cache-dir -r requirements.txt

# Copy your Django application code
COPY server .

# Expose port 8000
EXPOSE 8000

# Specify the command to run when the container starts
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
ENTRYPOINT ["tail", "-f", "/dev/null"]
