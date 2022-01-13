#!/usr/bin/env bash
set -e
SCRIPT_LOC=$(dirname "$0")

ACTION="up -d --scale megamolbart=4"
MODEL_DIR="/models"
CONFIG_DIR="/workspace/benchmark/cuchembm/config"

SOURCE_ROOT=.

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
  --stop | -s | stop)
    ACTION=stop
    shift
    ;;
  --config-dir | -c)
    CONFIG_DIR=$2
    shift
    shift
    ;;
  *)
    shift
    ;;
  esac
done

source ${SOURCE_ROOT}/.env

export CUCHEM_UI_START_CMD="python3 -m cuchembm --config-dir ${CONFIG_DIR}"
export MEGAMOLBART_CMD="bash -c 'python3 -m megamolbart'"

export WORKSPACE=/workspace
export MEGAMOLBART_PATH=/workspace/megamolbart
export NGINX_CONFIG=${PROJECT_PATH}/setup/config/nginx.conf
export PYTHONPATH_CUCHEM="${WORKSPACE}/common:${WORKSPACE}/common/generated"
export PYTHONPATH_CUCHEM="${PYTHONPATH_CUCHEM}:${WORKSPACE}/benchmark:${WORKSPACE}/cuchem:"

export PYTHONPATH_MEGAMOLBART="${WORKSPACE}/common:${WORKSPACE}/common/generated:${WORKSPACE}/megamolbart"
export PYTHONPATH_MEGAMOLBART="${PYTHONPATH_MEGAMOLBART}:${WORKSPACE}/benchmark:${WORKSPACE}/cuchem:"

docker-compose \
  -f ${SOURCE_ROOT}/setup/docker_compose.yml \
  --project-directory ${SOURCE_ROOT} \
  ${ACTION}