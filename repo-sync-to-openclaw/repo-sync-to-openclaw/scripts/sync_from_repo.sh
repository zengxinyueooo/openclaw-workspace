#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  sync_from_repo.sh --repo <repo_url_or_local_path> [--target <openclaw_dir>] [--dry-run]

Behavior:
  - clones or updates the migration repo in a temp dir
  - backs up current target workspace
  - syncs only safe content-layer paths
  - never overwrites environment-sensitive files like openclaw.json
EOF
}

REPO=""
TARGET="${HOME}/.openclaw"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="${2:-}"
      shift 2
      ;;
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$REPO" ]]; then
  echo "Missing --repo" >&2
  usage >&2
  exit 1
fi

if [[ ! -d "$TARGET" ]]; then
  echo "Target openclaw dir not found: $TARGET" >&2
  exit 1
fi

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

require_cmd git
require_cmd rsync
require_cmd mktemp

WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/repo-sync-openclaw.XXXXXX")"
REPO_DIR="${WORKDIR}/repo"
BACKUP_DIR="${TARGET}.backup.$(date +%Y%m%d-%H%M%S)"

cleanup() {
  rm -rf "$WORKDIR"
}
trap cleanup EXIT

if [[ -d "$REPO/.git" ]] || [[ -f "$REPO/.git" ]]; then
  git clone --depth 1 "$REPO" "$REPO_DIR"
else
  git clone --depth 1 "$REPO" "$REPO_DIR"
fi

echo "Repo staged at: $REPO_DIR"
echo "Target openclaw dir: $TARGET"
echo "Backup dir: $BACKUP_DIR"

if [[ $DRY_RUN -eq 1 ]]; then
  echo "[dry-run] Would back up target and sync the following if present:"
else
  cp -R "$TARGET" "$BACKUP_DIR"
fi

sync_dir() {
  local src_rel="$1"
  local dst_rel="$2"
  local src="${REPO_DIR}/${src_rel}"
  local dst="${TARGET}/${dst_rel}"

  if [[ ! -d "$src" ]]; then
    return 0
  fi

  mkdir -p "$dst"

  local -a rsync_args=(
    -av
    --exclude '.git/'
    --exclude '.openclaw/'
    --exclude '.env*'
    --exclude 'memory/'
    --exclude 'logs/'
    --exclude 'tmp/'
    --exclude 'cron-runs/'
    --exclude 'error_logs/'
    --exclude '.DS_Store'
  )

  if [[ $DRY_RUN -eq 1 ]]; then
    rsync_args+=(--dry-run)
  fi

  echo "Sync dir: ${src_rel} -> ${dst_rel}"
  rsync "${rsync_args[@]}" "${src}/" "${dst}/"
}

sync_file() {
  local src_rel="$1"
  local dst_rel="$2"
  local src="${REPO_DIR}/${src_rel}"
  local dst="${TARGET}/${dst_rel}"

  if [[ ! -f "$src" ]]; then
    return 0
  fi

  mkdir -p "$(dirname "$dst")"
  echo "Sync file: ${src_rel} -> ${dst_rel}"

  if [[ $DRY_RUN -eq 1 ]]; then
    return 0
  fi

  cp "$src" "$dst"
}

sync_dir "workspace" "workspace"
sync_dir "workspace-mcn-ant" "workspace-mcn-ant"
sync_dir "workspace-mcn-bee" "workspace-mcn-bee"
sync_dir "workspace-mcn-eagle" "workspace-mcn-eagle"
sync_dir "workspace-mcn-owl" "workspace-mcn-owl"
sync_dir "workspace-mcn-squirrel" "workspace-mcn-squirrel"
sync_dir "skills" "skills"

sync_file "cron/jobs.json" "cron/jobs.json"
sync_file "workspace/MEMORY.md" "workspace/MEMORY.md"
sync_file "workspace/NOTES.md" "workspace/NOTES.md"
sync_file "workspace-mcn-ant/MEMORY.md" "workspace-mcn-ant/MEMORY.md"
sync_file "workspace-mcn-bee/MEMORY.md" "workspace-mcn-bee/MEMORY.md"
sync_file "workspace-mcn-eagle/MEMORY.md" "workspace-mcn-eagle/MEMORY.md"
sync_file "workspace-mcn-owl/MEMORY.md" "workspace-mcn-owl/MEMORY.md"
sync_file "workspace-mcn-squirrel/MEMORY.md" "workspace-mcn-squirrel/MEMORY.md"

cat <<'EOF'
Skipped by design:
  - openclaw.json
  - agents/*/agent/models.json
  - agents/*/agent/auth-profiles.json
  - identity/
  - devices/
  - browser/
  - logs/
  - media/
  - tasks/
  - subagents/
  - agents/*/sessions/
  - .env*
  - .openclaw/

If the repo contains openclaw.json or other environment-sensitive files,
merge them manually after comparing with the current sandbox config.
EOF
