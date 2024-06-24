# Use the official Python 3.10 image with Ubuntu
FROM nvidia/cuda:12.5.0-devel-ubuntu20.04

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
    sqlite \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /server

# Copy the requirements file separately to leverage Docker cache
COPY requirements.txt .

USER root

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel

ENV PATH="/usr/local/cuda/bin:$PATH"
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:$LD_LIBRARY_PATH"
ENV FORCE_CMAKE=1

RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
RUN pip install llama_cpp_python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121 --force-reinstall --upgrade --no-cache-dir --verbose
RUN pip install -r requirements.txt

# Copy your Django application code
COPY . .

WORKDIR /
ENV UVICORN_HOST="0.0.0.0"
ENV UVICORN_PORT="8000"
EXPOSE 8000

ENTRYPOINT [ "uvicorn", "server.main:app", "--reload" ]
