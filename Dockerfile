FROM debian:jessie
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

RUN apt-get update && \
    apt-get install -y -qq --no-install-recommends python-pip git \
    build-essential nginx supervisor redis-server python-dev gcc \
    virtualenv mercurial file
RUN apt-get install -qq -y socat curl net-tools tmux less vim htop
RUN useradd equanimity
# RUN git clone https://github.com/AFDudley/btjs3.git /btjs3
RUN virtualenv venv
ADD . /equanimity
WORKDIR /equanimity
RUN rm -rf /equanimity/DBs; mkdir -p /equanimity/DBs/World
RUN mkdir /var/run/celery
RUN git checkout dev-docker
RUN . /venv/bin/activate; pip install -r requirements.txt; \
/usr/bin/supervisord -c /equanimity/config/supervisord.conf; tools/init_db.py

EXPOSE 8080
CMD ["/usr/bin/supervisord", "-n", "-c", "/equanimity/config/supervisord.conf"]
