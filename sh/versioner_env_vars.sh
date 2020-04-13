#!/bin/bash -Eeu

versioner_env_vars()
{
  docker run --rm cyberdojo/versioner:latest
  echo CYBER_DOJO_REPLER_IMAGE=cyberdojo/repler
  echo CYBER_DOJO_REPLER_CLIENT_PORT=9999
  echo CYBER_DOJO_REPLER_CLIENT_USER=nobody
  echo CYBER_DOJO_REPLER_SERVER_USER=root
}
