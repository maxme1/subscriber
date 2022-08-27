FROM continuumio/miniconda3

RUN apt-get update && apt-get install -y xvfb firefox-esr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /code

RUN conda install python==3.9.*
RUN pip install webdrivermanager && webdrivermanager firefox --linkpath /usr/local/bin

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN chmod +x run-celery.sh
ENV DISPLAY=:10
