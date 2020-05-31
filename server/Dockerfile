FROM  alpine:latest
LABEL maintainer=austin@sixty-north.com
LABEL maintainer=jon@jaggersoft.com

# Install base apps
RUN apk --update --no-cache add \
  bash \
  python3-dev \
  py3-pip

ARG CYBER_DOJO_REPLER_HOME
WORKDIR ${CYBER_DOJO_REPLER_HOME}

# Install python dependencies
COPY requirements.txt .
COPY install.sh .
RUN ./install.sh && rm ./install.sh

# Install the source code
COPY . .

ARG REPL_PORT
ENV REPL_PORT ${REPL_PORT}

ARG NETWORK_NAME
ENV NETWORK_NAME ${NETWORK_NAME}

ARG REPL_IMAGE_NAME
ENV REPL_IMAGE_NAME ${REPL_IMAGE_NAME}

ARG COMMIT_SHA
ENV SHA=${COMMIT_SHA}

ARG CYBER_DOJO_REPLER_PORT
ENV PORT=${CYBER_DOJO_REPLER_PORT}
EXPOSE ${PORT}

CMD [ "./up.sh" ]
