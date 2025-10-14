FROM docker.io/python:3.12.5-slim
COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

ENV HOME /home/pyuser 

RUN groupadd --system --gid 999 nonroot \ &&  \
    useradd --system --gid 999 --uid 999 --create-home pyuser

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR $HOME

ENV TMP /tmp

ENV PATH="$HOME/.venv/bin:$PATH"

RUN uv venv