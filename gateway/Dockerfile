FROM debian:buster-slim

ADD requirements.txt /app/

WORKDIR /app

RUN apt-get update && apt install -y gcc python3-setuptools python3-pip \
    && pip3 install --no-cache-dir -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*

ADD azure /root/.azure

ADD app.py conn_string.py /app/

EXPOSE 8080

CMD ["python3", "app.py"]