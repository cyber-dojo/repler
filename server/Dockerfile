FROM  alpine:latest
LABEL maintainer=austin@sixty-north.com

# - - - - - - - - - - - - - - - -
# install nodejs
# tar is needed to tar-pipe test coverage out of tmpfs.
# - - - - - - - - - - - - - - - -
RUN apk --update --no-cache add \
    bash \
    gcc \
    make \
    musl-dev \
    python3-dev \
    tar

ARG CYBER_DOJO_RUNNER_HOME
WORKDIR ${CYBER_DOJO_RUNNER_HOME}

COPY . ${CYBER_DOJO_RUNNER_HOME}
RUN pip3 install -r requirements.txt

ARG PORT
ARG REPL_PORT
ARG NETWORK_NAME
ARG REPL_IMAGE_NAME

EXPOSE ${PORT}

ENV PORT ${PORT}
ENV REPL_PORT ${REPL_PORT}
ENV NETWORK_NAME ${NETWORK_NAME}
ENV REPL_IMAGE_NAME ${REPL_IMAGE_NAME}

CMD [ "./up.sh" ]
