---
name: block-push-main
enabled: true
event: bash
pattern: git\s+push\s+.*\bmain\b
action: block
---

**Push to main blocked.**

You must never push directly to main. The flow is:
- Feature/fix/refactor branches → `develop` (via PR)
- `develop` → `main` (done manually by the user)

Pushing to main triggers a deployment. Only the user merges develop into main manually.
