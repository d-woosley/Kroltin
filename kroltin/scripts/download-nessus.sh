#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y curl jq

# Use the HOME_DIR from Packer if provided; otherwise default to current $HOME
BASE_DIR="${HOME_DIR:-$HOME}"
DOWNLOAD_DIR="${BASE_DIR}/Downloads"
mkdir -p "$DOWNLOAD_DIR"

LATEST_NESSUS_FILE="$(
  curl -fsSL https://www.tenable.com/downloads/api/v1/public/pages/nessus |
  jq -r '.products
    | to_entries
    | map(select(.value.version!=null))
    | max_by(.value.version|split(".")|map(tonumber))
    | .value.downloads
    | map(select(.meta_data.os_type=="Debian" and .meta_data.arch=="amd64"))
    | first.file'
)"

curl -fsSL \
  -o "${DOWNLOAD_DIR}/${LATEST_NESSUS_FILE}" \
  "https://www.tenable.com/downloads/api/v2/pages/nessus/files/${LATEST_NESSUS_FILE}"
