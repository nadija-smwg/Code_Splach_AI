# ClearanceX Agent Rules

This file defines critical rules that all AI assistants (like yourself) must follow when interacting with the ClearanceX repository.

## ⛔ Git Restrictions (CRITICAL)

Per the `Docs/Git_Branching_Strategy.md` and CodeSplash'26 hackathon guidelines, you must strictly follow these git practices when assisting a user:

1. **NEVER use `git add .` or `git add -A`**. 
   - You must add files individually and explicitly (e.g., `git add frontend/src/components/Button.tsx`).
   - Adding all files blindly can result in "one giant commit at the end" which is strictly forbidden and will get the team disqualified.

2. **Commit Frequently and granularly**.
   - Do not batch multiple unrelated changes into a single commit.
   - If you help the user with multiple files, commit them separately based on their logical function.

3. **Strict Commit Message Format**:
   - Every commit message must follow this format: `type(module): Phase XX - short description`
   - Example: `feat(ai): Phase 03 - document classifier with 7 document types`
   - Example: `fix(api): Phase 14 - fix discrepancy endpoint null handling`

4. **Never squash commits**.
   - Do not use tools or commands that squash commit histories together. The judges need to see the raw, detailed commit history from each team member.

By following these rules, you will help the team maintain a compliant, professional repository that meets the hackathon's strict evaluation criteria.
