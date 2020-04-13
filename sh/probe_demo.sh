#!/bin/bash -Eeu

readonly SH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SH_DIR}/build_images.sh"
source "${SH_DIR}/containers_up.sh"
source "${SH_DIR}/containers_down.sh"
source "${SH_DIR}/ip_address.sh"
source "${SH_DIR}/versioner_env_vars.sh"
export $(versioner_env_vars)
readonly IP_ADDRESS="$(ip_address)" # slow

#- - - - - - - - - - - - - - - - - - - - - - - - - - -
main()
{
  build_images
  container_up nginx
  sleep 1
  echo; demo
  containers_down
}

#- - - - - - - - - - - - - - - - - - - - - - - - - - -
demo()
{
  demo_new_route__probing_non_JSON
}

demo_new_route__probing_non_JSON()
{
  echo 'API:new probing (non JSON)'
  curl_200 GET "$(controller)/alive?"
  curl_200 GET "$(controller)/ready?"
  curl_200 GET "$(controller)/sha"
  echo
}

#- - - - - - - - - - - - - - - - - - - - - - - - - - -
curl_200()
{
  local -r log=/tmp/repler.log
  local -r type="${1}"   # eg GET|POST
  local -r route="${2}"  # eg repler/ready
  curl  \
    --fail \
    --request "${type}" \
    --silent \
    --verbose \
      "http://${IP_ADDRESS}:$(port)/${route}" \
      > "${log}" 2>&1

  grep --quiet 200 "${log}"             # eg HTTP/1.1 200 OK
  local -r result=$(tail -n 1 "${log}") # eg {"sha":"78c19640aa43ea214da17d0bcb16abbd420d7642"}
  echo "$(tab)${type} ${route} => 200 ${result}"
}

#- - - - - - - - - - - - - - - - - - - - - - - - - - -
port() { printf 80; }
controller() { echo -n repler; }
tab() { printf '\t'; }

#- - - - - - - - - - - - - - - - - - - - - - - - - - -
main
