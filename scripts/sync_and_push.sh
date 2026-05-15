#!/usr/bin/env bash
# sync_and_push.sh — safe git sync
# Usage: ./scripts/sync_and_push.sh <branch>

set -euo pipefail

BRANCH="${1:-main}"

echo "==> Fetching origin..."
git fetch origin

echo "==> Pulling with rebase from origin/${BRANCH}..."
git pull --rebase origin "${BRANCH}"

echo "==> Pushing to origin/${BRANCH}..."
git push origin "${BRANCH}"

echo "==> Done."