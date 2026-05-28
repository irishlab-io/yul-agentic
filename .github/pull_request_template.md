## Summary

<!-- One-line description of what this PR does -->

Closes #<!-- issue number -->

---

## Type of Change

- [ ] 🐛 Bug fix
- [ ] ✨ New feature
- [ ] ♻️ Refactor (no functional change)
- [ ] 🔒 Security fix
- [ ] 🧪 Test improvement
- [ ] 📝 Documentation
- [ ] 🤖 AI-generated (review carefully)

---

## Review Checklist

- [ ] Code follows project style (ruff, 128-char line length, PEP 257 docstrings, `typing` annotations)
- [ ] All existing tests pass: `uv run pytest`
- [ ] Test coverage is ≥92%
- [ ] Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) format
- [ ] No new security vulnerabilities introduced
- [ ] If AI-generated: I have read and verified every changed line

### If Models / Database Changed

- [ ] Django migration is included
- [ ] Migration is reversible or irreversibility is documented

### If This is an AI-Generated PR

- [ ] I have reviewed **all** AI-generated changes — not just the summary
- [ ] No intentional teaching vulnerabilities were accidentally removed
- [ ] The fix matches what was requested in the linked issue
- [ ] I am satisfied this PR is safe to merge

---

## Testing Evidence

<!-- Paste relevant pytest output or describe manual testing steps -->

```
uv run pytest
```
