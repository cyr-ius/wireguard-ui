# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-alpine

# set version label
ARG BUILD_DATE
ARG VERSION
ARG WIREGUARDUI_RELEASE
LABEL build_version="version:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="cyr-ius"

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install dependencies
RUN apk add --no-cache --virtual build build-base python3-dev libffi-dev zlib-dev jpeg-dev tiff-dev freetype-dev
RUN apk add --no-cache zlib jpeg tiff wireguard-tools iptables

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# clean content
RUN apk del build

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

WORKDIR /app
COPY app /app/app
COPY migrations /app/migrations

ARG VERSION
ENV VERSION ${VERSION}

EXPOSE 8000/tcp
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn","app:create_app()"]