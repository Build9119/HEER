#!/bin/bash
# download_skills.sh — Download curated JARVIS skills from Nivalia/JARVIS-skills
# into .agents/skills/ preserving full directory structure.
set -euo pipefail

REPO="Nivalia/JARVIS-skills"
BRANCH="main"
DEST=".agents/skills"
API="https://api.github.com/repos/${REPO}/contents"

# Curated skills relevant to HEER (AI agency operating system)
SKILLS=(
  web-search
  code-review
  document-parser
  email-sender
  report-generator
  meeting-summary
  pdf-processor
  speech-to-text
  text-to-speech
  github
  database-admin
  security-audit
  project-manager
  social-media
  keyword-research
  file-manager
  content-generator
  translate-agent
  video-processor
  image-generate
  weather
  code-generator
  api-test
  monitoring
  healthcheck
  docker-cli
  kubernetes
  contract-review
  note-taker
  session-logs
)

mkdir -p "$DEST"

# Recursively download a directory from GitHub
download_dir() {
  local path="$1"
  local outdir="$2"
  local items
  items=$(curl -s "${API}/${path}" | jq -r '.[] | "\(.type)\t\(.name)\t\(.download_url // "")"')
  while IFS=$'\t' read -r type name url; do
    [ -z "$name" ] && continue
    if [ "$type" = "dir" ]; then
      download_dir "${path}/${name}" "${outdir}/${name}"
    elif [ "$type" = "file" ]; then
      mkdir -p "$outdir"
      echo "  ↓ ${path}/${name}"
      curl -sL "$url" -o "${outdir}/${name}"
    fi
  done <<< "$items"
}

for skill in "${SKILLS[@]}"; do
  echo "==> ${skill}"
  download_dir "$skill" "${DEST}/${skill}"
done

echo ""
echo "Done. Skills installed in ${DEST}/"
find "$DEST" -name SKILL.md | wc -l | xargs echo "SKILL.md files:"