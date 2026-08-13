# CVE-2020-14343

A vulnerability was discovered in the PyYAML library in versions before 5.4, where it is susceptible to arbitrary code execution when it processes untrusted YAML files through the `full_load` method or with the `FullLoader` loader. Applications that use the library to process untrusted input may be vulnerable to this flaw. This flaw allows an attacker to execute arbitrary code on the system by abusing the `python/object/new` constructor. This flaw is due to an incomplete fix for GHSA-6757-jp84-gxfx.

## Affected component

`pyproject.toml` → `pyyaml==5.3.1`

## Finding

PyYAML before 5.4 is vulnerable to [CVE-2020-14343](https://nvd.nist.gov/vuln/detail/CVE-2020-14343). When `full_load()` or the `FullLoader` loader parses untrusted YAML, the `python/object/new` constructor can be abused to execute arbitrary code on the host. This is an incomplete fix for GHSA-6757-jp84-gxfx.

The pin in `pyproject.toml` is `5.3.1`, which is below the fixed 5.4.

## Severity

|                     |                                                |
|---------------------|------------------------------------------------|
| CVSS 3.1 base score | **9.8 (Critical)**                             |
| Vector              | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |
| Fixed in            | PyYAML 5.4                                     |

## Why it matters here

`src/feature_flags.py` (`load_flags()`) reads a YAML file whose path comes from the `FEATURE_FLAGS_FILE` environment variable, so the parser can reach content that is not fully under the application's control.

## Suggested fix

Bump `pyyaml` to `>=5.4` in `pyproject.toml`, then regenerate the lock file.  In reality `PyYAML 6.x.x` has been out for a few years and we should just migrate to the next major semantic version.

## References

- [GitHub Advisory](https://github.com/advisories/GHSA-8q59-q68h-6hv4)
- [National Vulnerability Database](https://nvd.nist.gov/vuln/detail/CVE-2020-14343)
