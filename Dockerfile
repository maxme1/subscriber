FROM python:3.8

WORKDIR /code
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

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

RUN apt-get update -y \
  && apt-get -y install \
    xvfb \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/*
RUN Xvfb :10 -ac &
RUN export DISPLAY=:10

CMD ["python", "./app.py"]
