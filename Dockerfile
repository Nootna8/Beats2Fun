FROM python:3.9
WORKDIR /app

RUN apt-get update && apt-get install -y \
  build-essential \
  libgtk-3-dev

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt