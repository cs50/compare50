# we use cs50/baseimage for publish50
# it has Python 3.6 installed
# but can be simpler image if you prefer (e.g., ubuntu:17.04)
# just be sure it has python installed at least
FROM cs50/baseimage

# become root
USER root

# mysql
RUN apt-get -qq update && \
    apt-get dist-upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        libmysqlclient-dev \
        mysql-server

# rabbitmq (can be something else)
# http://docs.celeryproject.org/en/latest/getting-started/brokers/
RUN wget https://packages.erlang-solutions.com/erlang-solutions_1.0_all.deb && \
    dpkg -i erlang-solutions_1.0_all.deb && rm -f erlang*.deb && curl -s \
    https://packagecloud.io/install/repositories/rabbitmq/rabbitmq-server/script.deb.sh | bash && \
    apt-get install -y rabbitmq-server

# celery and mysql client
RUN pip install celery mysqlclient

# celery daemon
# http://docs.celeryproject.org/en/latest/userguide/daemonizing.html
RUN wget https://raw.githubusercontent.com/celery/celery/3.1/extra/generic-init.d/celeryd --output-document=/etc/init.d/celeryd
RUN chmod a+x /etc/init.d/celeryd

# script with example celery task
WORKDIR /root/
COPY celery_demo.py .
COPY celery_app.py .

# celery daemon configurations
# http://docs.celeryproject.org/en/latest/userguide/daemonizing.html#available-options

# name of python script containing celery app
ENV CELERY_APP="celery_app"

# path for celery binary
ENV CELERY_BIN="/opt/pyenv/shims/celery"

# allow celery to creat directories
ENV CELERY_CREATE_DIRS=1

# change to this directory before running celery
ENV CELERYD_CHDIR="/root/"

# group to run celery as
ENV CELERYD_GROUP="root"

# path for celery log file
ENV CELERYD_LOG_FILE="/var/log/celery.log"

# have many celery workers
# http://docs.celeryproject.org/en/latest/userguide/workers.html
ENV CELERYD_NODES=1

# how many tasks per worker
ENV CELERYD_OPTS="--concurrency=1"

# user to run celery as
ENV CELERYD_USER="root"

# start mysql server
# create database for celery to store task metadata in
# start queue service
# start celery service
# run a simple task
CMD service mysql start && \
    mysql -e "CREATE DATABASE IF NOT EXISTS celerydb;" && \
    service rabbitmq-server start && \
    /etc/init.d/celeryd start && \
    python celery_demo.py
