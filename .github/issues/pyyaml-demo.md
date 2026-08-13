# CVE-2020-14343

A vulnerability was discovered in the PyYAML library in versions before 5.4, where it is susceptible to arbitrary code execution when it processes untrusted YAML files through the `full_load` method or with the `FullLoader` loader. Applications that use the library to process untrusted input may be vulnerable to this flaw. This flaw allows an attacker to execute arbitrary code on the system by abusing the `python/object/new` constructor. This flaw is due to an incomplete fix for GHSA-6757-jp84-gxfx.

| | |
|---|---|
| CVSS 3.1 base score | **9.8 (Critical)** |
| Vector | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |
| Affected versions | PyYAML `< 5.4` |
| Fixed in | PyYAML `5.4` |
| Source | [NVD](https://nvd.nist.gov/vuln/detail/CVE-2020-14343) |

## Where it appears in this project

`pyproject.toml` pins `pyyaml==5.3.1`, which is below the fixed 5.4 and therefore in range.

This is a realistic SCA result and an open item in the remediation backlog, so it exercises the full triage-to-fixer chain end to end.

Note that `docs/VULNERABILITIES.md` §16 is out of date on this row. It lists PyYAML **3.12** with CVE-2017-18342 and CVE-2019-20477, which does not match the version actually pinned in `pyproject.toml`.

Scope: this report covers the **dependency** only. The `yaml.load(fh, Loader=yaml.Loader)` call in `src/feature_flags.py` is a separate, already-catalogued weakness (CWE-502, `docs/VULNERABILITIES.md`) and is not part of this finding.

## Prerequisites — create the missing labels

Run once per repository. The `agentic-workflows` label does not exist yet, so `gh issue create --label agentic-workflows` fails with `'agentic-workflows' not found` until you create it.

```bash
gh label create "agentic-workflows" --color ededed --description "Handled by an agentic workflows"
gh label create "severity:critical" --color b60205 --description "Critical severity"
gh label create "severity:high" --color d93f0b --description "High severity"
gh label create "severity:medium" --color fbca04 --description "Medium severity"
gh label create "severity:low" --color 0e8a16 --description "Low severity"
```

The repository already has `agentic-workflows` (plural). That is **not** the same label — `.github/workflows/aw-triage.md` allows the singular `agentic-workflows`, and the four `severity:*` labels above, in its `safe-outputs.add-labels.allowed` list.

## File the issue

```bash
gh issue create --title "[security] pyyaml 5.3.1 is vulnerable" --body-file .github/issues/pyyaml-report.md --label agentic-workflows
```

Confirm it landed:

```bash
gh issue view <number> --web
```

## What happens next

1. **`AW - Triage`** fires on `issues: opened` and delegates to the `triage-analyst` agent. Expect the `security` and `severity:critical` labels, plus one short guidance comment. The comment should stay generic — responsible disclosure means it will not restate exploit detail.
2. Applying `security` triggers **`AW - Fixer`**, which delegates to the `software-engineer` agent.
3. **Expected outcome: a draft PR that bumps the pin.** Dependency and SCA version bumps are in scope (see `.github/agents/software-engineer.agent.md`), so the fixer should edit `pyyaml==5.3.1` in `pyproject.toml`, regenerate `uv.lock`, run the suite, and open a draft `ai/`-prefixed PR with the `security-reviewer` verdict in the body. A comment deferring to Dependabot is the wrong result.
