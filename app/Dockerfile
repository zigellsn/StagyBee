FROM stagybee/python-base:slim 

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV DEPENDENCIES="gcc \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    libc-dev"

ADD requirements/common.txt $TMP
ADD requirements/dev.txt $TMP

RUN apt-get update && apt-get install -y --no-install-recommends gettext libpq5 $DEPENDENCIES && \
    pip install --no-cache-dir -r $TMP/dev.txt && \
    apt-get autoremove -y --purge $DEPENDENCIES && \
    rm -rf /var/lib/apt/lists/* && \
    rm -f $TMP/common.txt && \
    rm -f $TMP/dev.txt

USER pyuser

ADD --chown=pyuser:users . .
ADD entrypoint.sh .

ENTRYPOINT ["/home/pyuser/entrypoint.sh"]