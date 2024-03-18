# Use the official Python 3.10 image with Alpine Linux
FROM python:3.10-alpine
LABEL authors="janle"

RUN apk update && apk add --no-cache gcc musl-dev python3-dev
RUN pip install --upgrade pip && pip install --upgrade --quiet setuptools cython
RUN pip install --upgrade --quiet langchain langchain-community langchainhub
RUN pip install --upgrade pgvector

RUN pip install pypdf


