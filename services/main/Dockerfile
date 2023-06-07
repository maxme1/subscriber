FROM continuumio/miniconda3:23.3.1-0-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /code

RUN conda install python==3.10.*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY services/main/*.py .
COPY . .
