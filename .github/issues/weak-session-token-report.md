# CWE-330

Use of Insufficiently Random Values. The product uses insufficiently random numbers or values in a security context that depends on unpredictable numbers. When the product generates predictable values in a context requiring unpredictability, it may be possible for an attacker to guess the next value that will be generated, and use this guess to impersonate another user or access sensitive information.

## Affected component

`src/utils.py` → `generate_session_token()`

## Finding

Session tokens are derived from the user id and the wall-clock time, hashed with MD5:

```python
token_string = f"{user_id}_{time.time()}"
return hashlib.md5(token_string.encode()).hexdigest()
```

Neither input is secret. `user_id` is a small sequential integer, and `time.time()` is a float with microsecond resolution, so an attacker who knows roughly when a victim logged in has on the order of a few million candidates to enumerate offline — trivially fast against MD5. There is no server-side entropy in the token at all.

`check_authentication()` in `src/auth.py` reads `session_token` straight from the request cookie and looks it up, so a correctly guessed token is accepted as a full session with no additional check.

## Severity

|                     |                                                     |
|---------------------|-----------------------------------------------------|
| CVSS 3.1 base score | **7.5 (High)**                                      |
| Vector              | `CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N`      |
| Remediation         | Generate tokens from a CSPRNG (`secrets`)           |

## Why it matters here

Two things make this worse than the token weakness on its own:

- `hash_password()` in the same module also uses MD5 (CWE-327, `docs/VULNERABILITIES.md` §11), so a forged session and a cracked password hash reinforce each other.
- `logout()` in `src/auth.py` returns success without deleting the session row, so a guessed or stolen token stays valid indefinitely (CWE-613). There is no expiry column check anywhere in the lookup path.

The net effect is a durable account takeover primitive that needs no credential and leaves no failed-login trail.

## Suggested fix

Use the standard library CSPRNG and drop MD5 from the token path entirely:

```python
import secrets

def generate_session_token(user_id):
    return secrets.token_urlsafe(32)
```

Alongside it:

- Invalidate sessions on logout — `logout()` should delete the row the way `logout_user()` already does.
- Move password hashing to bcrypt or argon2 (tracked as CWE-327, §11 — out of scope for this issue, but the same module).
- Consider recording an expiry on the `sessions` row and rejecting stale tokens at lookup time.

## References

- [CWE-330: Use of Insufficiently Random Values](https://cwe.mitre.org/data/definitions/330.html)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [Python `secrets` module](https://docs.python.org/3/library/secrets.html)
- `docs/VULNERABILITIES.md` §11
