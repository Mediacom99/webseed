---
name: protect-database-bash
enabled: true
event: bash
action: block
pattern: (rm|mv|cp|cat\s*>|truncate|>)\s*.*webseed\.json
---

**Database file operation blocked.**

You are attempting to delete, move, overwrite, or truncate `webseed.json` via a shell command. This is the TinyDB database and must never be destroyed or overwritten. Use the `store.py` API for all database operations.
