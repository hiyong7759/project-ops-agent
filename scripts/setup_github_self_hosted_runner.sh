#!/usr/bin/env bash
set -euo pipefail

OWNER="${GITHUB_OWNER:-hiyong7759}"
REPO="${GITHUB_REPO:-project-ops-agent}"
RUNNER_TOKEN="${RUNNER_TOKEN:-}"
RUNNER_DIR="${RUNNER_DIR:-.runner/github-actions-runner}"
RUNNER_LABELS="${RUNNER_LABELS:-project-ops-agent,codex-cli,wsl,self-hosted}"
RUNNER_NAME="${RUNNER_NAME:-$(hostname)-project-ops-agent}"

if [ -z "$RUNNER_TOKEN" ]; then
  echo "RUNNER_TOKEN is required."
  echo "GitHub repo > Settings > Actions > Runners > New self-hosted runner에서 발급된 token을 RUNNER_TOKEN으로 넘겨주세요."
  exit 1
fi

mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

if [ ! -f ./config.sh ]; then
  latest_json="$(curl -fsSL https://api.github.com/repos/actions/runner/releases/latest)"
  runner_version="$(
    printf '%s' "$latest_json" \
      | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"].lstrip("v"))'
  )"
  archive="actions-runner-linux-x64-${runner_version}.tar.gz"
  url="https://github.com/actions/runner/releases/download/v${runner_version}/${archive}"
  curl -fL "$url" -o "$archive"
  tar xzf "$archive"
fi

./config.sh \
  --url "https://github.com/${OWNER}/${REPO}" \
  --token "$RUNNER_TOKEN" \
  --name "$RUNNER_NAME" \
  --labels "$RUNNER_LABELS" \
  --work "_work" \
  --unattended \
  --replace

echo
echo "Runner configured."
echo "Start it with:"
echo "  cd $RUNNER_DIR && ./run.sh"
