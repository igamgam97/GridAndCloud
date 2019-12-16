FROM debian:buster-slim

ADD app.py requirements.txt conn_string.py /app/

ADD azure /root/.azure

WORKDIR /app

RUN apt-get update && apt install -y gcc python3-setuptools python3-pip \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 8080

CMD ["python", "app.py"]