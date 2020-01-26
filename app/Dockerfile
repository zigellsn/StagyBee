FROM stagybee/python-base:slim 

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV DEPENDENCIES="gcc \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    libc-dev"

ADD requirements.txt $TMP

RUN apt-get update && apt-get install -y --no-install-recommends gettext $DEPENDENCIES && \
    pip install --no-cache-dir -r $TMP/requirements.txt && \
    apt-get autoremove -y --purge $DEPENDENCIES && \
    rm -rf /var/lib/apt/lists/* && \
    rm -f $TMP/requirements.txt

USER pyuser

ADD --chown=pyuser:users . .
ADD entrypoint.sh .

ENTRYPOINT ["/home/pyuser/entrypoint.sh"]