FROM python:3.10-slim
MAINTAINER Luca Petrillo "lucapetrillo99@gmail.com"

RUN apt-get update && apt-get install -y curl
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN groupadd -r worker && useradd -r -s /bin/false -g worker worker

COPY --chown=app:app . /app

ENTRYPOINT ["python", "main.py"]
