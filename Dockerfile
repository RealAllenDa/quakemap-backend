FROM v7odpsx0.mirror.aliyuncs.com/library/python:3.10

WORKDIR /code

ARG environment=development
ARG refresh_token

RUN echo "Building in environment ${environment}"

COPY ./requirements.txt /code/requirements.txt

RUN pip config set global.index-url http://mirrors.aliyun.com/pypi/simple
RUN pip config set install.trusted-host mirrors.aliyun.com
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code/
COPY ./config/$environment.yaml /code/config/$environment.yaml

ENV ENV=$environment
ENV REFRESH_TOKEN=$refresh_token
RUN apt-get update && \
    apt-get install -yq tzdata && \
    ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

ENV TZ="Asia/Shanghai"

ENTRYPOINT [ "python", "main.py" ]