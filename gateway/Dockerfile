FROM debian:buster-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3 python3-pip python3-setuptools \
    && rm -rf /var/lib/apt/lists/*

ADD service/* app.py requirements.txt /app/

ADD azure /root/.azure

WORKDIR /app

EXPOSE 8080

CMD ["python", "app.py"]