#!/bin/bash
set -euo pipefail
cd "${DEPLOY_PATH:?DEPLOY_PATH is required}"
exec 9>.deploy.lock
flock -n 9
compose=(docker compose -f docker-compose.prod.yml)
"${compose[@]}" build
"${compose[@]}" up -d --wait postgres
"${compose[@]}" run --rm --no-deps api uv run alembic upgrade head
"${compose[@]}" up -d --wait
retry_health() {
    local attempt
    for attempt in {1..30}; do
        if "$@"; then return 0; fi
        sleep 2
    done
    return 1
}
retry_health "${compose[@]}" exec -T nginx wget -q -O /dev/null http://127.0.0.1/
retry_health "${compose[@]}" exec -T api python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8000/openapi.json", timeout=10)'
