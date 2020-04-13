FROM  alpine:latest
LABEL maintainer=austin@sixty-north.com
LABEL maintainer=jon@jaggersoft.com

# Install os-provided packages
RUN apk --update --no-cache add \
  bash \
  gcc \
  g++ \
  make \
  musl-dev \
  python3-dev

ARG CYBER_DOJO_RUNNER_HOME
WORKDIR ${CYBER_DOJO_RUNNER_HOME}

# Install python dependencies
COPY requirements.txt ${CYBER_DOJO_RUNNER_HOME}
RUN pip3 install -r requirements.txt

# Install the rest of the source code
COPY . ${CYBER_DOJO_RUNNER_HOME}

ARG REPL_PORT
ARG NETWORK_NAME
ARG REPL_IMAGE_NAME

ENV REPL_PORT ${REPL_PORT}
ENV NETWORK_NAME ${NETWORK_NAME}
ENV REPL_IMAGE_NAME ${REPL_IMAGE_NAME}

ARG COMMIT_SHA
ENV SHA=${COMMIT_SHA}


ARG CYBER_DOJO_REPLER_PORT
ENV PORT=${CYBER_DOJO_REPLER_PORT}
EXPOSE ${PORT}

CMD [ "./up.sh" ]
