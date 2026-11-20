# Codex Instructions

- Implement the smallest correct solution.
- Focus on executable Python logic.
- Locate relevant symbols with `rg` before reading files; inspect narrow ranges and expand only when needed.
- Do not reread unchanged files or repeat diagnostics already established in the current task.
- Keep command output decision-focused: prefer quiet modes, targeted tests and filtered errors over full logs.
- Inspect repository structure incrementally; do not inventory unrelated directories or load generated data.
- Use only tools relevant to the current task and keep tool results concise.
- Avoid unnecessary classes, abstractions and dependencies.
- Do not refactor unrelated code.
- Preserve existing behaviour unless asked to change it.
- Write comments only for non-obvious decisions.
- Do not generate extra documentation unless requested.
- Run relevant tests after changes.
- Report passing suites as counts; include detailed output only for failures that affect the next action.
- Fix root causes, never hide failures.
- Never claim tests passed without running them.
- Keep final responses under 100 words.
- Report only changes, test results and blockers.
