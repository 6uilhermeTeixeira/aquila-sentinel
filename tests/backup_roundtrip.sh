#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
restored_db="sentinel_restore_test_$$"
cleanup() {
  docker compose -f compose/compose.yaml exec -T -u postgres postgres dropdb -U keycloak --if-exists "$restored_db" >/dev/null
}
trap cleanup EXIT
snapshot=$(python3 scripts/backup.py postgres)
python3 scripts/restore.py postgres "$snapshot" --database "$restored_db"
original=$(docker compose -f compose/compose.yaml exec -T -u postgres postgres psql -U keycloak -d keycloak -Atc 'select count(*) from realm')
restored=$(docker compose -f compose/compose.yaml exec -T -u postgres postgres psql -U keycloak -d "$restored_db" -Atc 'select count(*) from realm')
[ "$original" -gt 0 ]
[ "$original" = "$restored" ]
