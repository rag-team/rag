# Use the official Python 3.10 image with Ubuntu
FROM nvidia/cuda:11.6.2-base-ubuntu20.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND=noninteractive


# Update and upgrade packages
# RUN apt update && apt upgrade -y

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    gcc \
    git \
    g++ \
    # For mysqlclient
    python3-dev \
    libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /server

# Copy the requirements file separately to leverage Docker cache
COPY freeze.txt .
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel

ENV CMAKE_ARGS="-DLLAMA_CUBLAS=on -DLLAMA_ALL_WARNINGS=off"
RUN pip install "llama_cpp_python==0.2.60" --force-reinstall --upgrade --no-cache-dir --verbose
RUN pip install -r freeze.txt
RUN pip install -r requirements.txt

# Copy your Django application code
COPY . .

WORKDIR /
ENV UVICORN_HOST="0.0.0.0"
ENV UVICORN_PORT="8000"
EXPOSE 8000

ENTRYPOINT [ "uvicorn", "server.main:app", "--reload" ]
