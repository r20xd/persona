#!/usr/bin/env bash
# Project-scoped defaults; no global configuration or permission changes.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"

exec codex \
  -C "$repo_root" \
  -c 'model="gpt-6.1-sol"' \
  -c 'model_reasoning_effort="high"' \
  -c 'agents.enabled=true' \
  -c 'agents.default_subagent_model="gpt-6.1-sol"' \
  -c 'agents.default_subagent_reasoning_effort="low"' \
  -c 'agents.max_concurrent_threads_per_session=1' \
  "$@"
