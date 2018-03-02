#!/bin/bash

readonly ROOT_DIR="$( cd "$( dirname "${0}" )" && cd .. && pwd )"

docker build -t cyberdojo/runner_repl_base -f ${ROOT_DIR}/server/Dockerfile.base ${ROOT_DIR}/server
docker-compose --file ${ROOT_DIR}/docker-compose.yml build
