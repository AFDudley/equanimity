FROM debian:jessie
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

RUN apt-get update && \
    apt-get install -y --no-install-recommends python-pip git build-essential \
    python-dev gcc virtualenv mercurial

RUN virtualenv venv
#RUN ls
ADD . /equanimity
WORKDIR /equanimity
RUN git checkout docker
RUN . /venv/bin/activate; pip install -r requirements.txt
# RUN . /venv/bin/activate; ./setup.py test --nose-only

