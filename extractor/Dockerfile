FROM docker.io/eclipse-temurin:20-jre-jammy

ENV EXTRACTOR_VERSION 1.0.20
ENV KTOR_USER ktor
ENV HOME /home/$KTOR_USER
RUN set -ex \
    && buildDeps=' \
    wget \
    ca-certificates' \
    && apt-get update && apt-get install -y $buildDeps --no-install-recommends \
    && wget -O StagyBeeExtractor.tar https://github.com/zigellsn/StagyBeeExtractor/releases/download/v"${EXTRACTOR_VERSION}"/StagyBeeExtractor-"${EXTRACTOR_VERSION}".tar \
    && tar -xvf StagyBeeExtractor.tar \
    && apt-get purge -y --auto-remove $buildDeps \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home $KTOR_USER \
    && mkdir $HOME/app \
    && cp -R /StagyBeeExtractor-"${EXTRACTOR_VERSION}"/* $HOME/app \
    && chown -R $KTOR_USER $HOME/app \
    && rm -rf /StagyBeeExtractor \
    && rm /StagyBeeExtractor.tar

USER $KTOR_USER
WORKDIR $HOME/app/bin

EXPOSE 8443

ENTRYPOINT [ "./StagyBeeExtractor" ]