# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.2

FROM python:${PYTHON_VERSION}-slim

LABEL fly_launch_runtime="flask"

WORKDIR /code

RUN apt update && apt install --no-install-recommends -y git

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN git clone --single-branch --branch demo_texts https://github.com/sonofmun/CJH_Test_Data.git && cd CJH_Test_Data && git pull

COPY . .

EXPOSE 8080

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=8080"]
