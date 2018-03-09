FROM cs50/server
EXPOSE 8080

# rabbitmq (can be something else)
# http://docs.celeryproject.org/en/latest/getting-started/brokers/
RUN wget https://packages.erlang-solutions.com/erlang-solutions_1.0_all.deb && \
    dpkg -i erlang-solutions_1.0_all.deb && rm -f erlang*.deb && curl -s \
    https://packagecloud.io/install/repositories/rabbitmq/rabbitmq-server/script.deb.sh | bash && \
    apt-get install -y rabbitmq-server

# compression utilities
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        p7zip-full \
        libmysqlclient-dev \
        ncompress \
        unrar

COPY ./requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt && rm -f /tmp/requirements.txt

# celery daemon
# http://docs.celeryproject.org/en/latest/userguide/daemonizing.html
RUN wget https://raw.githubusercontent.com/celery/celery/3.1/extra/generic-init.d/celeryd --output-document=/etc/init.d/celeryd

RUN chmod a+x /etc/init.d/celeryd

# celery daemon configurations
# http://docs.celeryproject.org/en/latest/userguide/daemonizing.html#available-options

# name of python script containing celery app
ENV CELERY_APP="tasks"

# path for celery binary
ENV CELERY_BIN="/opt/pyenv/shims/celery"

# allow celery to creat directories
ENV CELERY_CREATE_DIRS=1

# change to this directory before running celery
ENV CELERYD_CHDIR="/var/www/"

# # group to run celery as
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

# CMD service rabbitmq-server start && \
#     rabbitmqctl status && \
#     service celeryd start && \
#     passenger start

CMD service rabbitmq-server start && \
    /etc/init.d/celeryd start && \
    passenger start
