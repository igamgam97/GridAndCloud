FROM conchoid/docker-detekt-cli:1.2.1-artifacts as detekt-cli

FROM debian:buster-slim

RUN for i in $(seq 1 8); do mkdir -p "/usr/share/man/man${i}"; done \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    python3 openjdk-11-jre openjdk-11-jdk git python3-pip python3-setuptools\
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/share/man/*

COPY --from=detekt-cli /detekt/detekt-cli /detekt

VOLUME /src

ADD main.py requirements.txt conn_string.py /app/

WORKDIR /app

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "main.py"]



