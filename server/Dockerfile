FROM  docker:latest
LABEL maintainer=austin@sixty-north.com

# - - - - - - - - - - - - - - - -
# install nodejs
# tar is needed to tar-pipe test coverage out of tmpfs.
# - - - - - - - - - - - - - - - -

RUN apk --update --no-cache add \
bash \
g++ \
make \
nodejs \
python \
tar

ARG            CYBER_DOJO_RUNNER_HOME
WORKDIR      ${CYBER_DOJO_RUNNER_HOME}

# RUN apk --update add --virtual build-dependencies build-base \
# && bundle config --global silence_root_warning 1 \
# && bundle install \
# && gem clean \
# && apk del build-dependencies build-base \
# && rm -vrf /var/cache/apk/*

# - - - - - - - - - - - - - - - -
# setup server
# - - - - - - - - - - - - - - - -

COPY . ${CYBER_DOJO_RUNNER_HOME}
RUN npm install

ARG PORT
EXPOSE ${PORT}
ENV PORT=${PORT}

# CMD [ "./up.sh" ]
CMD ["npm", "start"]
