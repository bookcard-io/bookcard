#!/usr/bin/env bash
set -euo pipefail

LOCKFILE="web/package-lock.json"
MANIFEST="web/package.json"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not inside a git repository" >&2
  exit 2
fi

staged_files="$(git diff --cached --name-only)"

lockfile_staged=false
manifest_staged=false

if echo "${staged_files}" | grep -Fxq "${LOCKFILE}"; then
  lockfile_staged=true
fi
if echo "${staged_files}" | grep -Fxq "${MANIFEST}"; then
  manifest_staged=true
fi

if [ "${lockfile_staged}" = "true" ] && [ "${manifest_staged}" = "false" ]; then
  cat >&2 <<'EOF'
error: web/package-lock.json is staged but web/package.json is not.

This usually means the lockfile was rewritten accidentally (toolchain drift or `npm install`).

Fix options:
- If you didn't intend to change dependencies: revert the lockfile change, then use `npm ci`.
- If you DID intend to change dependencies: make sure web/package.json is updated and staged too.
EOF
  exit 1
fi
