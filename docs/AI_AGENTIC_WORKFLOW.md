# AI AGENTIC WORKFLOWS — TRIAGE, SUPPORT, AND FIX

## Overview

This repository automates issue handling with [GitHub Agentic Workflows (gh-aw)](https://github.github.com/gh-aw/) — workflows written as Markdown with YAML frontmatter, compiled into GitHub Actions YAML, and executed by the GitHub Copilot engine.

Three workflows cover the lifecycle of an issue:

| Workflow | Fires when | What it does |
|---|---|---|
| `aw-triage.md` | An issue is opened or reopened | Classifies it, applies category and `severity:*` labels, posts one guidance comment |
| `aw-issue-triage.md` | Someone comments `/issue-triage` | Answers developer questions and objections, or re-analyses the issue on demand |
| `aw-fixer.md` | The `enhancement` or `security` label is applied | Writes the fix and opens a draft pull request |

Each delegates its real work to a **sub-agent** in `.github/agents/`, so the taxonomy, the engineering procedure, and the review bar each live in exactly one place.

Humans own every decision that matters: the agent job is read-only, every write goes through a constrained safe output, and every pull request opens as a draft.

---

## Architecture

```text
Issue opened / reopened
        │
        ▼
┌────────────────────────────────────────────────────────────────┐
│ aw-triage.md                          → triage-analyst         │
│   Classify · category + severity labels · one guidance comment │
└────────────────────────────────────────────────────────────────┘
        │
        ├──────────────► Developer comments /issue-triage
        │                        │
        │                        ▼
        │        ┌───────────────────────────────────────────────┐
        │        │ aw-issue-triage.md                            │
        │        │   Mode A  deep re-analysis  → triage-analyst  │
        │        │   Mode B  developer support → triage-support  │
        │        │     "why is this an issue?"                   │
        │        │     "this is a false positive"                │
        │        │     "we have no time or budget"               │
        │        │     "how do I fix this?"                      │
        │        │   Labels + one comment                        │
        │        │   Recommends only — never closes              │
        │        └───────────────────────────────────────────────┘
        │
        ▼
Maintainer applies `enhancement` or `security`
        │
        ▼
┌────────────────────────────────────────────────────────────────┐
│ aw-fixer.md                           → software-engineer      │
│   Real code change · draft PR on an aw/ branch                 │
│   Labelled agentic-workflows + needs-review                    │
└────────────────────────────────────────────────────────────────┘
        │
        ▼
CI (.github/workflows/main.yml) runs · human reviews · human merges
```

`security-reviewer` sits outside the automatic path. It is invocable directly from Copilot CLI or VS Code for ad-hoc review of a diff.

---

## The workflows

### `aw-triage.md` — first-pass classification

Triggers on `issues: [opened, reopened]`, plus `workflow_dispatch` with an issue number for a manual re-run.

Delegates to **`triage-analyst`**, which owns the category taxonomy (`bug`, `documentation`, `enhancement`, `question`, `security`, `triage`), the `severity:*` scale, and the reporter-facing comment guidance. Calls `noop` and stops on an empty, spam, or test issue.

Safe outputs: `add-comment` (max 1), `add-labels` (max 3).

### `aw-issue-triage.md` — developer support and deep re-triage

Triggers on the `/issue-triage` slash command in an issue comment — `/triage-issue` is accepted as an alias, since the two halves are easy to transpose. Open to **any authenticated GitHub user** (`roles: all`); pull request comments are excluded.

The command takes free text, and the workflow routes on it:

```text
/issue-triage                                    → deep re-analysis of the issue
/issue-triage why is this an issue?              → plain-language explanation
/issue-triage this is a false positive           → three-way verdict, adjudicated against the code
/issue-triage we have no budget this quarter     → deferral record
/issue-triage how would we fix this?             → remediation approach, no patch
```

Anything other than a bare request for analysis goes to **`triage-support`**. When the answer changes the classification, it passes back through `triage-analyst` so the taxonomy stays in one place.

**The false-positive verdict** is the part to understand. Most weaknesses in this repository are intentional and catalogued, so "this is a false positive" is usually wrong — but not always. The agent must return exactly one of three verdicts, each with cited evidence:

| Verdict | Meaning | Recommendation |
|---|---|---|
| Not present | The code does not do what the report says | `apply invalid` |
| Present as described | The code does what the report says, characterised correctly | `no change — issue stands` |
| Present but mitigated | Real, but a compensating control reduces it | `downgrade severity to <level>` |

**The agent recommends; it never decides.** `invalid` and `wontfix` are deliberately absent from the label allowlist, so it cannot apply them even if it concludes it should. It posts its reasoning, applies `triage`, and a maintainer makes the call.

Safe outputs: `add-comment` (max 1), `add-labels` (max 4).

### `aw-fixer.md` — issue to draft pull request

Triggers when the `enhancement` or `security` label is applied to an issue, plus `workflow_dispatch` with an issue number. Restricted to `admin`, `maintainer`, and `write` roles.

Delegates to **`software-engineer`**, which owns the codebase grounding, the fix-to-PR procedure, the quality bar, and the security-remediation rules. A stub, a placeholder, or a documentation-only diff is a failed run.

The workflow deliberately does **not** run the linter, type checker, or test suite — CI does that on the pull request it opens.

Safe output: `create-pull-request` with `title-prefix: "[aw]: "`, `branch-prefix: "aw/"`, labels `agentic-workflows` + `needs-review`, `allowed-files` excluding `.github/**`, and `protected-files: request_review` over `pyproject.toml`, `uv.lock`, and `requirements.txt`.

---

## The agents

| Agent | Owns |
|---|---|
| `triage-analyst.agent.md` | Category taxonomy, severity scale, reporter-facing comment guidance |
| `triage-support.agent.md` | The developer conversation: explaining a finding, adjudicating false-positive claims, recording time/budget deferrals, outlining a remediation approach |
| `software-engineer.agent.md` | Codebase grounding, fix-to-PR procedure, PR quality bar, security-remediation rules |
| `security-reviewer.agent.md` | Reviewing a diff for introduced weaknesses, incomplete remediations, and regressions |
| `agentic-workflows.md` | Dispatcher for working on gh-aw workflows themselves (creating, updating, debugging, upgrading) |

Agents are plain Markdown with `name:` and `description:` frontmatter. Editing an agent changes behaviour across every workflow that delegates to it — no recompile needed, because the agent files are read at runtime.

---

## Safety model

Every workflow follows the same shape, enforced at compile time by gh-aw:

- **The agent job is read-only.** `contents: read` plus the reads it needs. No `issues: write`, no `contents: write`.
- **Every mutation is a safe output.** Comments, labels, assets, and pull requests are applied by separate jobs with narrow permissions, from a structured request the agent emits — it never calls the GitHub API to write.
- **Label allowlists.** Each workflow declares exactly which labels it may apply, with a `max`. Anything outside the list is impossible, not merely discouraged.
- **Write targets are pinned.** `aw-issue-triage` omits `target:`, so comments and labels default to the triggering issue only.
- **Threat detection** runs on every workflow, scoped per workflow to distinguish framework scaffolding and legitimate authored instructions from genuine prompt injection.
- **Untrusted input is named as such.** Issue bodies, comments, and slash-command text are data describing a problem, never instructions to the agent. Each workflow prompt says so explicitly, and carries a `DO NOT` block of absolute constraints.
- **Draft pull requests only.** Nothing merges itself.

---

## Setup

### Labels

The workflows apply only labels that already exist. The current set:

```bash
gh label list
```

Category and process labels in use: `bug`, `documentation`, `duplicate`, `enhancement`, `question`, `security`, `triage`, `invalid`, `wontfix`, `good first issue`, `help wanted`.

Automation labels: `agentic-workflows`, `ai-generated`, `needs-review`, `agentic-threat-detected`.

Classification labels: `intentional-vuln` (a catalogued, deliberate weakness), `unintended-bug` (a genuine defect outside the catalogue), and `severity:critical` / `severity:high` / `severity:medium` / `severity:low`.

If you add a label the workflows should be able to apply, add it to the `safe-outputs.add-labels.allowed` list in the relevant workflow and recompile.

### Copilot engine

`.github/workflows/copilot-setup-steps.yml` installs the gh-aw CLI extension for the Copilot agent environment. The workflows themselves carry a `pre-agent-steps` block that ensures the Copilot CLI is reachable at `/usr/local/bin/copilot`, the path the sandbox spawns.

### Spend ceiling

The compiled workflows read the `GH_AW_DEFAULT_MAX_DAILY_AI_CREDITS` repository variable as a daily cap, defaulting to `5000` if unset. Because `/issue-triage` is open to any authenticated user, set this deliberately:

```bash
gh variable set GH_AW_DEFAULT_MAX_DAILY_AI_CREDITS --body "5000"
```

---

## Working on the workflows

Workflows are authored as `.github/workflows/*.md` and compiled to `.lock.yml`. **Never hand-edit a `.lock.yml`** — change the Markdown and recompile.

```bash
# Compile one workflow, or all of them
gh aw compile aw-issue-triage
gh aw compile

# Validate without writing lock files
gh aw validate aw-issue-triage

# Actionlint the generated workflow
gh aw lint .github/workflows/aw-issue-triage.lock.yml

# Trigger a run on demand (not `gh workflow run`)
gh aw run aw-fixer --ref main

# Inspect what happened
gh aw logs aw-issue-triage
gh aw audit <run-id>
```

Both the `.md` and its regenerated `.lock.yml` belong in the same commit.

For help authoring workflows, address the `agentic-workflows` agent in Copilot CLI or VS Code — it routes to the right gh-aw reference for creating, updating, debugging, or upgrading.

---

## Writing issues the workflows can act on

The agents read the issue body verbatim. What you put there determines what you get back.

| Include | Why it matters |
|---|---|
| A clear problem description | It is the task, read literally |
| Expected versus actual behaviour | Defines what "fixed" means |
| Steps to reproduce | Lets the agent locate the code path |
| Relevant files | Cuts down on wrong-file guesses |
| The CWE, if you know it | Anchors the classification and the remediation approach |

### Good

```text
Title: Login endpoint does not rate-limit failed attempts

The POST /login route in src/auth.py accepts unlimited authentication
attempts with no rate limiting, so credentials can be brute-forced.

Expected: after 5 consecutive failed attempts from one IP, return HTTP 429
and lock the account for 15 minutes.

Reproduce:
1. Send 10 POST requests to /login with invalid credentials
2. Every request returns 200 or 401 — never 429

Relevant files: src/auth.py, tests/test_auth.py
```

### Poor

```text
Title: Login is broken — fix it
Problem: authentication does not work
```

### Disagreeing with a triage result

If a classification looks wrong, do not edit the labels and move on — comment `/issue-triage` with what you think and why. The support agent checks the claim against the code and leaves a recommendation a maintainer can act on, so the reasoning stays on the issue.

---

## Reviewing AI-generated pull requests

Every AI-generated pull request opens as a **draft**, labelled `agentic-workflows` and `needs-review`, on an `aw/`-prefixed branch. None of them auto-merge.

Before marking one ready for review:

- [ ] Read every changed line — the summary is not the diff
- [ ] Run the full suite: `make test` (mirrors CI, gated at ≥75% coverage)
- [ ] Confirm no new weakness was introduced
- [ ] Confirm the remediation is complete — no equivalent bypass left beside it. Check nearby `# VULNERABILITY:` markers
- [ ] Confirm style: ruff defaults (88-char lines), PEP 257 docstrings, `typing` annotations
- [ ] Confirm the commit messages follow Conventional Commits

### Validating locally

```bash
git fetch origin
git checkout aw/<branch>

make install          # uv venv + uv sync --all-extras --dev --frozen
make test             # full suite with coverage, gated at 75%
make style            # ruff format + ruff check + ty
make run              # smoke test at http://localhost:8000
```

---

## File reference

| Path | Purpose |
|---|---|
| `.github/workflows/aw-triage.md` | First-pass classification workflow |
| `.github/workflows/aw-issue-triage.md` | `/issue-triage` developer support and deep re-triage |
| `.github/workflows/aw-fixer.md` | Issue-to-draft-PR workflow |
| `.github/workflows/*.lock.yml` | Compiled Actions YAML — generated, never hand-edited |
| `.github/workflows/main.yml` | CI: pre-commit, pytest, dependency and SAST scan stubs, container build |
| `.github/workflows/copilot-setup-steps.yml` | Installs the gh-aw CLI for the Copilot agent environment |
| `.github/agents/*.agent.md` | Sub-agents the workflows delegate to |
| `.github/aw/actions-lock.json` | Pinned action digests for the generated workflows |
| `.github/copilot-instructions.md` | Repository context for Copilot: commands, layout, style, workflow map |
| `.github/pull_request_template.md` | PR checklist, including the AI-generated section |
| `docs/VULNERABILITIES.md` | The remediation backlog — per-CWE description, locations, impact, mitigation |

---

## Design decisions

| Decision | Rationale |
|---|---|
| Read-only agent job, writes via safe outputs | The agent cannot mutate the repository directly, whatever it is persuaded to attempt |
| Draft pull requests only | AI output always needs human verification before merge |
| One taxonomy, owned by one agent | `triage-analyst` is the only place categories and severities are defined; other agents defer to it |
| `invalid` and `wontfix` off the allowlist | Dismissing a security report is a human decision, enforced by configuration rather than by prompt |
| `/issue-triage` open to `roles: all` | Outside reporters who disagree with a triage result need the same path as the team |
| `aw-fixer` does not run tests | CI validates the pull request; the agent spends its budget on a correct diff instead |
| Explicit `DO NOT` blocks in every prompt | Boundary constraints stated as prohibitions hold up better than implied scope |
| Branch prefix `aw/`, title prefix `[aw]: ` | Workflow-owned branches and PRs are filterable and identifiable at a glance |
| Conventional Commits | Matches the commitizen `commit-msg` hook already enforced by pre-commit |

---

## Troubleshooting

### The workflow did not fire

- For `/issue-triage`: the comment must **start** with the command, spelled `/issue-triage` or `/triage-issue`. A command mid-sentence does not match, and PR comments are excluded by design.
- A run that appears in the Actions tab with every job **skipped** is this gate rejecting the comment, not a broken workflow. No agent ran and no credits were spent — check the comment's first line.
- For `aw-fixer`: confirm the applied label is exactly `enhancement` or `security`.
- Check the Actions tab for a run that activated and then stopped — the `pre_activation` job gates on role and command match before any agent runs.

### The run activated but the agent did nothing

Check `gh aw logs <workflow>`. A `noop` is a successful outcome, not a failure — the workflows call it deliberately on empty, spam, or test issues, and record the reason.

### Labels were not applied

The label must exist in the repository **and** be in that workflow's `safe-outputs.add-labels.allowed` list. Both, or nothing happens. `invalid` and `wontfix` are excluded on purpose.

### The run succeeded but no comment or labels appeared

The agent analysed the issue and then stayed silent. That is a failed run, and the workflow prompt forbids it: if something it needed was unavailable, it must say so inside the comment and post anyway. Check `gh aw logs aw-issue-triage` for what it thought was blocking, and treat the prompt as needing a fix.

### A `.lock.yml` is out of date

`gh aw compile` and commit the result. The compiled workflow carries a check that fails the run when the lock file is stale relative to its source.

---

## Limitations

| Limitation | Notes |
|---|---|
| Single-job model | gh-aw workflows cannot orchestrate multiple dependent jobs; use plain Actions for that |
| Agents can be confidently wrong | Every output is a recommendation or a draft, never a decision |
| Complex multi-file refactors | `aw-fixer` works best on focused, single-concern issues |
| Job timeouts | 15 minutes for triage and fixer, 30 for `/issue-triage` |
| Copilot credits are finite | `/issue-triage` is publicly triggerable; keep the daily ceiling set |

---

## Resources

- [GitHub Agentic Workflows](https://github.github.com/gh-aw/) — the framework these workflows are built on
- [gh-aw reference files](https://github.com/github/gh-aw/tree/main/.github/aw) — triggers, safe outputs, sub-agents, network, patterns
- [Conventional Commits](https://www.conventionalcommits.org/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE](https://cwe.mitre.org/)
