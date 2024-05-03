FROM python:3.11-alpine3.17

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /code

COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache

COPY services/main/*.py .
COPY . .
