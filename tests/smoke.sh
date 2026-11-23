#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/bootstrap.py
docker compose -f compose/compose.yaml config --quiet
docker compose -f compose/compose.yaml up -d
for attempt in $(seq 1 150); do
  if curl --silent --fail http://127.0.0.1:8080/realms/master/.well-known/openid-configuration >/dev/null; then
    break
  fi
  sleep 2
done
curl --silent --fail http://127.0.0.1:8080/realms/master/.well-known/openid-configuration >/dev/null
response=$(curl --silent --fail -H 'Content-Type: application/json' -d '{"input":{"subject":{"id":"anonymous","verified":false,"expires_at":9999999999},"resource":"secrets","action":"read"}}' http://127.0.0.1:8181/v1/data/sentinel/access/allow)
[ "$response" = '{"result":false}' ]
