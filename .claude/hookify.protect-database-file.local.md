---
name: protect-database-file
enabled: true
event: file
action: block
conditions:
  - field: file_path
    operator: regex_match
    pattern: webseed\.json$
---

**Database file modification blocked.**

You are attempting to edit or overwrite `webseed.json` directly. This is the TinyDB database and must never be modified or overwritten by file operations. Use the `store.py` API to interact with the database programmatically.
