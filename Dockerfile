FROM debian:jessie

RUN apt-get update && \
    apt-get install -y --no-install-recommends python-pip git build-essential \
    python-dev gcc
RUN git clone https://github.com/AFDudley/equanimity.git
RUN cd equanimity && git checkout docker && pip install -r requirements.txt
