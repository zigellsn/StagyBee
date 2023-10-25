FROM docker.io/python:3.12.0-slim

ENV HOME /home/pyuser 
RUN useradd --gid users --create-home pyuser
WORKDIR $HOME

ENV TMP /tmp
ENV VENV=/opt/venv

ONBUILD RUN python3 -m venv $VENV && \
    python3 -m venv --system-site-packages $VENV
ENV PATH="$VENV/bin:$PATH"
ONBUILD RUN pip install --upgrade --no-cache-dir pip
