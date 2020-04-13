#!/bin/bash -Eeu

readonly ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# - - - - - - - - - - - - - - - - - - -
container_up()
{
  local -r service_name="${1}"
  printf '\n'
  docker-compose \
    --file "${ROOT_DIR}/docker-compose.yml" \
    up \
    --detach \
    --force-recreate \
    "${service_name}"
}

# - - - - - - - - - - - - - - - - - - -

container_up nginx
sleep 1
