---
name: protect-prompts
enabled: true
event: file
action: block
conditions:
  - field: file_path
    operator: regex_match
    pattern: prompts/.*\.txt$
---

**Prompt template modification blocked.**

You are attempting to modify a prompt template file in `prompts/`. These templates are carefully tuned and must not be changed without explicit user approval.

**Ask the user first** before making any changes to prompt files.
