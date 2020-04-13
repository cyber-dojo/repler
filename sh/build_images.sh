#!/bin/bash -Eeu

readonly ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${ROOT_DIR}/sh/versioner_env_vars.sh"
source "${ROOT_DIR}/sh/image_sha.sh"
export $(versioner_env_vars)

#- - - - - - - - - - - - - - - - - - - - - - - -
build_images()
{
  export COMMIT_SHA="$(git_commit_sha)"
  docker-compose \
    --file ${ROOT_DIR}/docker-compose.yml \
    build \
    --build-arg CYBER_DOJO_REPLER_PORT=${CYBER_DOJO_REPLER_PORT}
  unset COMMIT_SHA
}

# - - - - - - - - - - - - - - - - - - - - - - - -
git_commit_sha()
{
  echo $(cd "${ROOT_DIR}" && git rev-parse HEAD)
}

# - - - - - - - - - - - - - - - - - - - - - - - -
assert_equal()
{
  local -r name="${1}"
  local -r expected="${2}"
  local -r actual="${3}"
  if [ "${expected}" != "${actual}" ]; then
    echo "ERROR: unexpected ${name} inside image"
    echo "expected: ${name}='${expected}'"
    echo "  actual: ${name}='${actual}'"
    exit 42
  fi
}

#- - - - - - - - - - - - - - - - - - - - - - - -
build_images
assert_equal SHA "$(git_commit_sha)" "$(image_sha)"




#!/bin/bash -Eeu

#readonly ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# build_images()
# {
#  docker-compose \
#    --file ${ROOT_DIR}/docker-compose.yml \
#    build
# }
