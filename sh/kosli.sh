#!/usr/bin/env bash
set -Eeu

export KOSLI_ORG=cyber-dojo
export KOSLI_FLOW=repler

readonly KOSLI_HOST_STAGING=https://staging.app.kosli.com
readonly KOSLI_HOST_PRODUCTION=https://app.kosli.com

# - - - - - - - - - - - - - - - - - - -
kosli_create_flow()
{
  local -r hostname="${1}"

  kosli create flow "${KOSLI_FLOW}" \
    --description "REPL for Python images" \
    --host "${hostname}" \
    --template artifact \
    --visibility public
}

# - - - - - - - - - - - - - - - - - - -
kosli_report_artifact()
{
  local -r hostname="${1}"

  pushd "$(root_dir)" > /dev/null

  kosli report artifact "$(artifact_name)" \
      --artifact-type docker \
      --host "${hostname}"

  popd > /dev/null
}

# - - - - - - - - - - - - - - - - - - -
kosli_assert_artifact()
{
  local -r hostname="${1}"

  kosli assert artifact "$(artifact_name)" \
      --artifact-type docker \
      --host "${hostname}"
}

# - - - - - - - - - - - - - - - - - - -
kosli_expect_deployment()
{
  local -r environment="${1}"
  local -r hostname="${2}"

  # In .github/workflows/main.yml deployment is its own job
  # and the image must be present to get its sha256 fingerprint.
  docker pull "$(artifact_name)"

  kosli expect deployment "$(artifact_name)" \
    --artifact-type docker \
    --description "Deployed to ${environment} in Github Actions pipeline" \
    --environment "${environment}" \
    --host "${hostname}"
}

# - - - - - - - - - - - - - - - - - - -
artifact_name()
{
  source "$(root_dir)/sh/echo_versioner_env_vars.sh"
  export $(echo_versioner_env_vars)
  echo "${CYBER_DOJO_REPLER_IMAGE}:${CYBER_DOJO_REPLER_TAG}"
}

# - - - - - - - - - - - - - - - - - - -
root_dir()
{
  # Functions in this file are called after sourcing (not including)
  # this file so root_dir() cannot use the path of this script.
  git rev-parse --show-toplevel
}

# - - - - - - - - - - - - - - - - - - -
on_ci_kosli_create_flow()
{
  if on_ci; then
    kosli_create_flow "${KOSLI_HOST_STAGING}"
    kosli_create_flow "${KOSLI_HOST_PRODUCTION}"
  fi
}

# - - - - - - - - - - - - - - - - - - -
on_ci_kosli_report_artifact()
{
  if on_ci; then
    kosli_report_artifact "${KOSLI_HOST_STAGING}"
    kosli_report_artifact "${KOSLI_HOST_PRODUCTION}"
  fi
}

# - - - - - - - - - - - - - - - - - - -
on_ci_kosli_assert_artifact()
{
  if on_ci; then
    kosli_assert_artifact "${KOSLI_HOST_STAGING}"
    kosli_assert_artifact "${KOSLI_HOST_PRODUCTION}"
  fi
}

# - - - - - - - - - - - - - - - - - - -
write_evidence_json()
{
  echo '{ "server": ' > "$(evidence_json_path)"
  cat "${ROOT_DIR}/test/reports/coverage.json" >> "$(evidence_json_path)"
  echo ', "client": ' >> "$(evidence_json_path)"
  cat "${ROOT_DIR}/client/test/reports/coverage.json" >> "$(evidence_json_path)"
  echo '}' >> "$(evidence_json_path)"
}

# - - - - - - - - - - - - - - - - - - -
evidence_json_path()
{
  echo "${ROOT_DIR}/test/reports/evidence.json"
}

# - - - - - - - - - - - - - - - - - - - - - - - -
on_ci()
{
  [ -n "${CI:-}" ]
}
