#!/bin/bash -Eeu

readonly ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# - - - - - - - - - - - - - - - - - - -
container_down()
{
  docker-compose \
    --file "${ROOT_DIR}/docker-compose.yml" \
    down \
    --remove-orphans \
    --volumes
}

# - - - - - - - - - - - - - - - - - - -
container_down
