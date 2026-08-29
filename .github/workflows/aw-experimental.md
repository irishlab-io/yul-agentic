---
name: AW - A/B Experimental Flow
run-name: "Agentic Workflows - Slash A/B experimental workflow on issue #${{ github.event.issue.number }} for ${{ github.repository }} by ${{ github.actor }}"

on:
  slash_command:
    name:
      - experiment
    events:
      - issue_comment
  roles: all
  reaction: eyes

model: gpt-5.4-mini
engine:
  id: copilot
timeout-minutes: 30

tools:
  github:
    mode: gh-proxy
    toolsets:
      - issues

network:
  allowed:
    - defaults

pre-agent-steps:
  - name: Ensure Copilot CLI exists at the path the sandbox spawns
    shell: bash
    run: |
      set -euo pipefail
      if [ -x /usr/local/bin/copilot ]; then
        echo "/usr/local/bin/copilot already present - nothing to do"
        exit 0
      fi
      resolved="$(command -v copilot || true)"
      if [ -z "$resolved" ]; then
        echo "::error::copilot CLI not found on PATH"
        exit 1
      fi
      echo "Installing wrapper: /usr/local/bin/copilot -> ${resolved}"
      wrapper="$(mktemp)"
      printf '#!/usr/bin/env bash\nexec "%s" "$@"\n' "$resolved" > "$wrapper"
      sudo install -m 0755 "$wrapper" /usr/local/bin/copilot
      rm -f "$wrapper"
      /usr/local/bin/copilot --version

permissions:
  contents: read
  issues: read

safe-outputs:
  add-comment:
    max: 1

experiments:
  style: [concise, detailed]
---

You are summarizing the issue this command was invoked on.

{{#if experiments.style == 'concise' }}
Summarize this issue in **two sentences or fewer**. No headings, no bullet lists.
{{/if}}

{{#if experiments.style == 'detailed' }}
Summarize this issue in detail: what was reported, the reproduction steps,
the current state of the discussion, and what a maintainer should do next.
Use short headed sections.
{{/if}}

Post the summary as a comment on the issue.
