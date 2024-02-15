FROM python:3.10

WORKDIR /code

ARG environment=development
ARG refresh_token
ARG sentry_url
ARG database_url
ARG dmdata_webhook_url

RUN echo "Building in environment ${environment}"

COPY ./requirements.txt /code/requirements.txt

RUN pip config set global.index-url http://mirrors.aliyun.com/pypi/simple
RUN pip config set install.trusted-host mirrors.aliyun.com
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code/
COPY ./config/$environment.yaml /code/config/$environment.yaml

ENV ENV=$environment
ENV SENTRY_URL=$sentry_url
ENV REFRESH_TOKEN=$refresh_token
ENV DATABASE_URL=$database_url
ENV DMDATA_WEBHOOK_URL=$dmdata_webhook_url
RUN sed -i 's#http://deb.debian.org#http://mirrors.163.com#g' /etc/apt/sources.list.d/debian.sources
RUN apt-get update && \
    apt-get install -yq tzdata && \
    ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

ENV TZ="Asia/Shanghai"

ENTRYPOINT [ "python", "main.py" ]