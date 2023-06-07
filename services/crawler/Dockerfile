FROM continuumio/miniconda3:23.3.1-0

# RUN apt-get update && apt-get install -y xvfb firefox-esr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DISPLAY=:10
WORKDIR /code

RUN conda install python==3.10.*
#RUN pip install webdrivermanager && webdrivermanager firefox --linkpath /usr/local/bin

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY services/crawler/*.py .
COPY . .
