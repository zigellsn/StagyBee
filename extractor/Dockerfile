FROM openjdk:8-jre-slim

ENV EXTRACTOR_VERSION 1.0.3
ENV KTOR_USER ktor
ENV HOME /home/$KTOR_USER
RUN set -ex \
    && buildDeps=' \
    wget \
    ca-certificates' \
    && apt-get update && apt-get install -y $buildDeps --no-install-recommends \
    && wget -O StagyBeeExtractor.tar https://github.com/zigellsn/StagyBeeExtractor/releases/download/v"${EXTRACTOR_VERSION}"/StagyBeeExtractor-shadow-"${EXTRACTOR_VERSION}".tar \
    && tar -xvf StagyBeeExtractor.tar \
    && apt-get purge -y --auto-remove $buildDeps \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home $KTOR_USER \
    && mkdir $HOME/app \
    && cp /StagyBeeExtractor-shadow-"${EXTRACTOR_VERSION}"/lib/StagyBeeExtractor.jar $HOME/app \
    && chown -R $KTOR_USER $HOME/app \
    && rm -rf /StagyBeeExtractor \
    && rm /StagyBeeExtractor.tar

WORKDIR $HOME/app
USER $KTOR_USER

EXPOSE 8080
EXPOSE 9090

ENTRYPOINT [ "java", "-server", "-XX:+UnlockExperimentalVMOptions", "-XX:+UseCGroupMemoryLimitForHeap", "-XX:InitialRAMFraction=2", "-XX:MinRAMFraction=2", "-XX:MaxRAMFraction=2", "-XX:+UseG1GC", "-XX:MaxGCPauseMillis=100", "-XX:+UseStringDeduplication", "-jar", "StagyBeeExtractor.jar" ]
