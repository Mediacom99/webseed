---
name: require-type-hints
enabled: true
event: file
action: block
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.py$
  - field: new_text
    operator: regex_match
    pattern: def\s+\w+\([^)]*\)\s*:
---

**Missing type hints on function signature.**

All function signatures in this project must include type hints for parameters and return type. Use the format:

```python
def function_name(param: type, param2: type) -> ReturnType:
```

Add proper type annotations before proceeding.
