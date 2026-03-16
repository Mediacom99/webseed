---
active: true
iteration: 1
session_id: 
max_iterations: 40
completion_promise: "ALL_STORIES_COMPLETE"
started_at: "2026-03-16T13:16:58Z"
---

ultrathink. Read PRD_REDESIGN.md. Find the next story with an unchecked
Status checkbox. Implement that story:

1. Read the story's acceptance criteria and files to create/modify
3. Run any tests or verification steps listed in the Testing section
4. If tests fail, fix and re-run until they pass
5. Check off all completed acceptance criteria and testing items in the PRD file
6. Run: git add -A && git commit -m '<commit message from the story>'
7. Mark the story's Status checkbox as checked: - [x]
8. Move to the next unchecked story

If ALL stories and checkpoints are complete:
- Output <promise>ALL_STORIES_COMPLETE</promise>

If you are stuck on a story after 3 attempts:
- Document what's blocking in a comment below the story
- Move to the next story if possible
- If not possible (dependency), output <promise>BLOCKED</promise>

