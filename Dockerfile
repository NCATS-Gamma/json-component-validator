# This Dockerfile is used to deploy the JSON Component Validator

FROM python:3

LABEL maintainer="patrick@covar.com"
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

ENV REFRESHED_AT 2019-03-25

## Install basic tools
RUN apt-get update
RUN apt-get install -yq \
    vim

## Set up home directory
RUN useradd -m -s /bin/bash murphy
WORKDIR /home/murphy

## Get ROBOKOP software
RUN git clone https://github.com/NCATS-Gamma/json-component-validator.git
WORKDIR /home/murphy/json-component-validator

## Install all requirements
RUN pip install -r ./requirements.txt --src /usr/local/src

## Finish up
ENV HOME=/home/murphy
ENV USER=murphy
ENV PYTHONPATH=/home/murphy/json-component-validator

WORKDIR /home/murphy/json-component-validator

ENTRYPOINT ["./server.py"]