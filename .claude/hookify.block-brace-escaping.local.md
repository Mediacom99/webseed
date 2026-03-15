---
name: block-brace-escaping
enabled: true
event: file
action: block
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.py$
  - field: new_text
    operator: contains
    pattern: 'replace("{", "{{")'
---

**Do NOT escape braces in values passed to `str.format()`.**

`str.format()` does NOT re-parse `{`/`}` inside substituted values. Escaping them with `.replace("{", "{{")` doubles braces in the output, corrupting prompts sent to Claude. This bug was fixed in commit 5c4bbf2 and must not be reintroduced.

If you need to protect literal braces in a **template** string, use `{{` and `}}` directly in the template file itself.
