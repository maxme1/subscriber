FROM ubuntu:bionic
#FROM python:3.8

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
    libnspr4 libnss3 lsb-release xdg-utils libxss1 libdbus-glib-1-2 \
    curl unzip wget \
    xvfb

WORKDIR /code
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

RUN GECKODRIVER_VERSION=`curl https://github.com/mozilla/geckodriver/releases/latest | grep -Po 'v[0-9]+.[0-9]+.[0-9]+'` && \
    wget https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz && \
    tar -zxf geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz -C /usr/local/bin && \
    chmod +x /usr/local/bin/geckodriver && \
    rm geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz

#RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.27.0/geckodriver-v0.27.0-linux64.tar.gz && \
#    tar -zxf geckodriver-v0.27.0-linux64.tar.gz -C /usr/local/bin && \
#    chmod +x /usr/local/bin/geckodriver && \
#    rm geckodriver-v0.27.0-linux64.tar.gz

RUN wget -O firefox-setup.tar.bz2 'https://download.mozilla.org/?product=firefox-latest&os=linux64' && \
    tar xjf firefox-setup.tar.bz2 -C /opt/ && \
    ln -s /opt/firefox/firefox /usr/bin/firefox && \
    rm firefox-setup.tar.bz2

#RUN wget -O firefox-setup.tar.bz2 https://ftp.mozilla.org/pub/firefox/releases/60.0/linux-x86_64/en-US/firefox-60.0.tar.bz2 && \
#    tar xjf firefox-setup.tar.bz2 -C /opt/ && \
#    ln -s /opt/firefox/firefox /usr/bin/firefox && \
#    rm firefox-setup.tar.bz2

COPY . .

#RUN /code/prepare-display.sh

RUN echo "#!/bin/bash\n" \
	 "Xvfb :10 -ac &\n" \
         "python3 ./app.py\n" > run.sh

#COPY run.sh run.sh
#RUN nohup bash -c "/code/prepare-display.sh &" && sleep 4

RUN chmod +x run.sh
ENV DISPLAY=:10
CMD ./run.sh
