#!/usr/bin/env bash

apt install curl jq -y
LATEST_NESSUS_FILE=$(curl -s 'https://www.tenable.com/downloads/api/v1/public/pages/nessus' | jq -r '.products|to_entries|map(select(.value.version!=null))|max_by(.value.version|split(".")|map(tonumber))|.value.downloads|map(select(.meta_data.os_type=="Debian" and .meta_data.arch=="amd64"))|first.file')
curl -sSL -o "~/Downloads/$LATEST_NESSUS_FILE" "https://www.tenable.com/downloads/api/v2/pages/nessus/files/$LATEST_NESSUS_FILE"
