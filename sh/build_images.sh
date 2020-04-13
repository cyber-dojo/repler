#!/bin/bash -Eeu

readonly ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

build_images()
{
  docker-compose \
    --file ${ROOT_DIR}/docker-compose.yml \
    build
}
