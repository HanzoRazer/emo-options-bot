#!/usr/bin/env bash
set -euo pipefail
if command -v pwsh >/dev/null 2>&1; then
  pwsh -File tools/repo_check.ps1 "$@"
elif command -v powershell >/dev/null 2>&1; then
  powershell -ExecutionPolicy Bypass -File tools/repo_check.ps1 "$@"
else
  echo "PowerShell is required. Install pwsh or powershell." >&2
  exit 2
fi