#!/usr/bin/env bash
set -euo pipefail
psql -h localhost -p 5433 -U werd -d werd_dev "$@"
