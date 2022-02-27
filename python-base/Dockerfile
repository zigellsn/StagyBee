FROM python:3.10.2-slim

ENV HOME /home/pyuser 
RUN useradd --create-home pyuser
WORKDIR $HOME

ENV TMP /tmp
ENV VENV=/opt/venv

ONBUILD RUN python3 -m venv $VENV && \
    python3 -m venv --system-site-packages $VENV
ENV PATH="$VENV/bin:$PATH"
ONBUILD RUN pip install --upgrade --no-cache-dir pip
