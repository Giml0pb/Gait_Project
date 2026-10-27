#!/usr/bin/env sh
set -eu
cd -- "$(dirname -- "$0")"
exec uv run python scripts/run_single_trial.py "$@"
