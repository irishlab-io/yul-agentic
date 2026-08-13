# CVE-2024-34069

Werkzeug is a comprehensive WSGI web application library. The debugger in affected versions of Werkzeug can allow an attacker to execute code on a developer's machine under some circumstances. This requires the attacker to get the developer to interact with a domain and subdomain they control, and enter the debugger PIN, but if they are successful it allows access to the debugger even if it is only running on localhost. This also requires the attacker to guess a URL in the developer's application that will trigger the debugger.

## Affected component

`pyproject.toml` → `werkzeug==2.2.3`

## Finding

Werkzeug before 3.0.3 is vulnerable to [CVE-2024-34069](https://nvd.nist.gov/vuln/detail/CVE-2024-34069). The interactive debugger's PIN protection can be defeated when a developer is lured to an attacker-controlled domain and subdomain, granting the attacker code execution in the context of the running application — even when the server is bound to localhost only.

The pin in `pyproject.toml` is `2.2.3`, which is below the fixed 3.0.3.

## Severity

|                     |                                                |
|---------------------|------------------------------------------------|
| CVSS 3.1 base score | **7.5 (High)**                                 |
| Vector              | `CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:H/A:H` |
| Fixed in            | Werkzeug 3.0.3                                 |

## Why it matters here

`src/config/config.py` sets `DEBUG = True` unconditionally, so the interactive debugger is live wherever this application runs. That turns a conditional development-only issue into a directly reachable one: any environment that picks up this config — including the container built by `Dockerfile` — serves the vulnerable debugger.

`docs/VULNERABILITIES.md` §12 already records `DEBUG = True` as an information disclosure weakness. This report is the dependency half of the same exposure and covers both, because bumping the pin alone leaves the debugger enabled.

## Suggested fix

1. Bump `werkzeug` to `>=3.0.3` in `pyproject.toml` and regenerate the lock file. Note that `flask==2.2.5` constrains Werkzeug to the 2.x line, so Flask needs to move to `>=3.0` at the same time — this is a coordinated bump, not a single-line edit.
2. Stop hardcoding debug mode. Default it off and let the environment opt in:

```python
DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
```

## References

- [GitHub Advisory](https://github.com/advisories/GHSA-2g68-c3qc-8985)
- [National Vulnerability Database](https://nvd.nist.gov/vuln/detail/CVE-2024-34069)
