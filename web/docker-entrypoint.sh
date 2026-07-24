#!/usr/bin/env bash
set -euo pipefail

if [[ ${1:-serve} != "serve" ]]; then
    exec "$@"
fi

web --host 127.0.0.1 --port 8001 &
backend_pid=$!
caddy run --config /etc/caddy/Caddyfile --adapter caddyfile &
caddy_pid=$!

shutdown() {
    status=$?
    trap - EXIT INT TERM
    kill -TERM "$backend_pid" "$caddy_pid" 2>/dev/null || true
    wait "$backend_pid" 2>/dev/null || true
    wait "$caddy_pid" 2>/dev/null || true
    exit "$status"
}

trap shutdown EXIT INT TERM
wait -n "$backend_pid" "$caddy_pid"
