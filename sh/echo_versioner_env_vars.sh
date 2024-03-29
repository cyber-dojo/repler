#!/usr/bin/env bash
set -Eeu

echo_versioner_env_vars()
{
  local -r sha="$(cd "$(root_dir)" && git rev-parse HEAD)"
  docker run --rm cyberdojo/versioner:latest

  echo CYBER_DOJO_REPLER_SHA="${sha}"
  echo CYBER_DOJO_REPLER_TAG="${sha:0:7}"

  echo CYBER_DOJO_REPLER_CLIENT_PORT=9999
  echo CYBER_DOJO_REPLER_CLIENT_USER=nobody
  echo CYBER_DOJO_REPLER_SERVER_USER=root
}
