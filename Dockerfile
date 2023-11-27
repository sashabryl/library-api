FROM python:3.11-slim-buster
LABEL maintainer="edlrian814@gmail.com"

ENV PYTHONUNBUFFERED=1

WORKDIR app/

RUN apt-get update -y \
    && apt-get install libpq-dev gcc -y

RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

RUN adduser \
    --disabled-password \
    --no-create-home \
    django-user

USER django-user
