#!/usr/bin/env bash
set -Eeu

image_sha()
{
  docker run --rm ${CYBER_DOJO_REPLER_IMAGE}:latest sh -c 'echo ${SHA}'
}
