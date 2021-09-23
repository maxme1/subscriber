FROM python:3.8

WORKDIR /code
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN GECKODRIVER_VERSION=`curl https://github.com/mozilla/geckodriver/releases/latest | grep -Po 'v[0-9]+.[0-9]+.[0-9]+'` && \
    wget https://github.com/mozilla/geckodriver/releases/download/$GECKODRIVER_VERSION/geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz && \
    tar -zxf geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz -C /usr/local/bin && \
    chmod +x /usr/local/bin/geckodriver && \
    rm geckodriver-$GECKODRIVER_VERSION-linux64.tar.gz

RUN wget -O firefox-setup.tar.bz2 'https://download.mozilla.org/?product=firefox-latest&os=linux64'
RUN tar xjf firefox-setup.tar.bz2 -C /opt/
RUN ln -s /opt/firefox/firefox /usr/bin/firefox
RUN rm firefox-setup.tar.bz2

COPY . .

RUN ./prepare-display.sh
CMD ["python", "./app.py"]
