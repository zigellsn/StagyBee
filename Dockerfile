FROM stagybee/python-base:slim 

ENV PYTHONUNBUFFERED 1

ENV DEPENDENCIES="gcc \
    libc-dev"

ADD requirements.txt $TMP

RUN apt-get update && apt-get install -y --no-install-recommends gettext $DEPENDENCIES && \
    pip install --no-cache-dir -r $TMP/requirements.txt && \
    apt-get autoremove -y --purge $DEPENDENCIES && \
    rm -rf /var/lib/apt/lists/* && \
    rm -f $TMP/requirements.txt

USER pyuser

ADD --chown=pyuser:users . . 

RUN python manage.py migrate --run-syncdb && \
    python manage.py compilemessages && \
    python manage.py collectstatic 

VOLUME ["/home/pyuser/static"]
