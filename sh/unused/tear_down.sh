#!/bin/bash

# During development, when a test fails it can leave containers around.
# I'd like to leave the container for a failed test un-removed since that way
# I can shell into it (eg for debugging). So I don't do a teardown at the
# end of each test. Instead I do a big teardown before all the tests run.

readonly PREFIX='test_run__runner_stateless_'

readonly ZOMBIE_CONTAINERS=$(docker ps --all --filter "name=${PREFIX}" --format "{{.Names}}")
if [ "${ZOMBIE_CONTAINERS}" != "" ]; then
  docker rm --force ${ZOMBIE_CONTAINERS}
fi
