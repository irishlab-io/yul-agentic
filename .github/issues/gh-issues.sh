#!/usr/bin/env bash
#
# Create the security test issues in .github/issues/ as GitHub issues.
#
# Each issue is filed with the `agentic-workflows` label, which is what
# `AW - Triage` listens for. Triage then applies `security` and the
# appropriate `severity:*` label, which in turn triggers `AW - Fixer`.
#
# Usage:
#   .github/issues/gh-issues.sh              # create them all
#   .github/issues/gh-issues.sh --dry-run    # print what would run
#   .github/issues/gh-issues.sh --cleanup    # close them again
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISSUE_DIR="$REPO_ROOT/.github/issues"
LABEL="agentic-workflows"

# file|title
ISSUES=(
  "pyyaml-code-execution.md|[security] pyyaml 5.3.1 is vulnerable (CVE-2020-14343)"
  "requests-proxy-auth-report.md|[security] requests 2.27.1 leaks Proxy-Authorization on redirect (CVE-2023-32681)"
  "sqli-auth-report.md|[security] SQL injection in authenticate_user() (CWE-89)"
  "weak-session-token-report.md|[security] Predictable session tokens in generate_session_token() (CWE-330)"
  "werkzeug-debugger-report.md|[security] werkzeug 2.2.3 debugger allows remote code execution (CVE-2024-34069)"
)

DRY_RUN=false
CLEANUP=false

usage() {
  sed -n '3,13p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

preflight() {
  command -v gh >/dev/null 2>&1 || {
    echo "error: the GitHub CLI (gh) is not installed - see https://cli.github.com/" >&2
    exit 1
  }
  gh auth status >/dev/null 2>&1 || {
    echo "error: gh is not authenticated - run: gh auth login" >&2
    exit 1
  }
}

ensure_labels() {
  echo "==> Ensuring labels exist"
  gh label create "$LABEL" --color ededed --description "Handled by an agentic workflow" 2>/dev/null || true
}

create_issues() {
  for entry in "${ISSUES[@]}"; do
    local file="$ISSUE_DIR/${entry%%|*}"
    local title="${entry#*|}"

    if [[ ! -f $file ]]; then
      echo "error: missing body file: $file" >&2
      exit 1
    fi

    if $DRY_RUN; then
      echo "gh issue create --title \"$title\" --body-file \"$file\" --label $LABEL"
      continue
    fi

    echo "==> $title"
    gh issue create --title "$title" --body-file "$file" --label "$LABEL"
  done
}

cleanup_issues() {
  local numbers
  numbers="$(gh issue list --label "$LABEL" --state open --limit 100 --json number --jq '.[].number')"

  if [[ -z $numbers ]]; then
    echo "No open issues labelled '$LABEL'."
    return
  fi

  for number in $numbers; do
    if $DRY_RUN; then
      echo "gh issue close $number --reason 'not planned'"
    else
      echo "==> Closing #$number"
      gh issue close "$number" --reason "not planned"
    fi
  done
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true ;;
    --cleanup) CLEANUP=true ;;
    -h | --help) usage 0 ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage 1
      ;;
  esac
  shift
done

$DRY_RUN || preflight

if $CLEANUP; then
  cleanup_issues
else
  $DRY_RUN || ensure_labels
  create_issues
fi
