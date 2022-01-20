FROM python:3.9-slim-buster

# GO ENV VARS
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/opt:${PYTHONPATH}"

WORKDIR /opt

RUN apt-get update \
  && apt-get -y install gcc netcat net-tools \
  && apt-get clean

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r ./requirements.txt

COPY ./ ./
ENTRYPOINT ["python", "./main.py"]
