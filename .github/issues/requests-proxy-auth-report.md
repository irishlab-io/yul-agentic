# CVE-2023-32681

Requests is an HTTP library. Since version 2.3.0, Requests has been leaking `Proxy-Authorization` headers to destination servers when redirected to an HTTPS endpoint. This is a product of how `rebuild_proxies` reattaches the `Proxy-Authorization` header to requests. For HTTP connections sent through the tunnel, the proxy will identify the header in the request itself and remove it prior to forwarding to the destination server. However when sent over HTTPS, the `Proxy-Authorization` header must be sent in the CONNECT request as the proxy has no visibility into the tunneled request. This results in Requests forwarding proxy credentials to the destination server unintentionally, allowing a malicious actor to potentially exfiltrate sensitive information.

## Affected component

`pyproject.toml` → `requests==2.27.1`

## Finding

Requests before 2.31.0 is vulnerable to [CVE-2023-32681](https://nvd.nist.gov/vuln/detail/CVE-2023-32681). When a request is redirected to an HTTPS endpoint, `rebuild_proxies()` reattaches the `Proxy-Authorization` header, which is then delivered to the destination server rather than being consumed by the proxy. Any actor controlling a redirect target can harvest the proxy credentials.

The pin in `pyproject.toml` is `2.27.1`, which is below the fixed 2.31.0.

## Severity

|                     |                                                |
|---------------------|------------------------------------------------|
| CVSS 3.1 base score | **6.1 (Medium)**                               |
| Vector              | `CVSS:3.1/AV:N/AC:H/PR:H/UI:N/S:C/C:H/I:N/A:N` |
| Fixed in            | requests 2.31.0                                |

## Why it matters here

`src/utils.py` (`fetch_url()`) issues `requests.get()` against a URL supplied by the caller and follows redirects with the library default. An attacker who can influence that URL only needs the response to redirect to an HTTPS host they control to receive whatever `Proxy-Authorization` value the environment supplies.

Scope: this report covers the **dependency** only. The absence of URL validation in `fetch_url()` (CWE-918) and the `verify=False` argument on the same call are separate, already-catalogued weaknesses — see `docs/VULNERABILITIES.md` §8 — and are not part of this finding.

## Suggested fix

Bump `requests` to `>=2.31.0` in `pyproject.toml` and regenerate the lock file. The 2.31.x line is API-compatible with 2.27.1 for the usage in this project, so no call-site changes are expected.

## References

- [GitHub Advisory](https://github.com/advisories/GHSA-j8r2-6x86-q33q)
- [National Vulnerability Database](https://nvd.nist.gov/vuln/detail/CVE-2023-32681)
