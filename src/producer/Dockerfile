# syntax = docker/dockerfile:1.2
FROM python:3.12.2-slim
LABEL maintainer="Vadim Kozyrevskiy" \
      email="vadikko2@mail.ru"
ENV TZ='Europe/Moscow'

# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get install --no-install-recommends -y git && \
    pip install --no-cache-dir --upgrade pip==24.* && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code/src

COPY ./requirements.txt /code/requirements.txt
RUN pip install -r /code/requirements.txt --root-user-action=ignore

COPY ./src/producer /code/src/producer

CMD ["python3", "-m", "producer.main"]
