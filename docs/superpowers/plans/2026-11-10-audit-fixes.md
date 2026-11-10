# Audit Fixes Implementation Plan

> Execute inline with the executing-plans and test-driven-development skills;
> obtain one independent review after implementation.

**Goal:** Implement the ten reviewed fixes without new dependencies.
**Architecture:** Keep Config/Engine/GUI/CLI; validate at their existing boundaries.
**Tech Stack:** Python 3.11+, Win32, CustomTkinter, unittest.
**Spec:** `docs/superpowers/specs/2026-11-10-audit-fixes-design.md`

## Global constraints

- Preserve existing user changes in `.agents/` and `skills-lock.json`.
- Mock OS input, hooks, focus and screen pixels in tests.
- Keep the fixes uncommitted for user review.

## Tasks

- [x] 1. Config: write failing tests for invalid load/save, key conflicts,
  exact config path and failed-write preservation. Add validation, warnings and
  serialized atomic saves in `core/config.py`; run the config suite.
- [x] 2. Engine: write failing tests for wrong executable/query failure,
  interrupted input/focus loss, manual origin, Extreme 1x, answer targeting,
  key release and stopped restart. Fix `core/engine.py`; run all tests.
- [x] 3. GUI/CLI: write failing tests for queued F12 closure and rejected key
  changes. Handle config warnings/errors and closure without Tk calls from
  listeners; update `gui.py` / `autoskip_dialogue.py`; run all tests.
- [x] 4. Cleanup/docs: remove unused helpers/imports, ignore and untrack generated
  bytecode, update README with actual behavior, config bounds and test command.
  Run syntax checks, unittest discovery, diff checks and independent review.

## Review focus

Process-query access denied; window closes between checks; pause/stop during
held input; saving config while another callback saves; generated input being
captured as a new hotkey; GUI closing with queued events. Add regression tests
where each behavior is implemented. Report remaining live-game limits.

## Progress

- Baseline: syntax/imports and direct dependencies pass; no source tests exist.
- Design decisions: implement directly in the shared checkout on a new local
  branch to make the user's requested fixes immediately reviewable. No worktree
  setup, merge, commit, dependency installation or publication is needed.
- Task 1 complete: config tests reproduced invalid values, hotkey conflicts,
  failed-write memory mutation and wrong save path; all 8 pass after fixes.
- Task 2 complete: engine tests reproduced the audit issues; full suite 30/30.
  Real read-only process-query smoke check also returned `python.exe` correctly.
- Task 3 complete: GUI callback tests reproduced F12, conflict-reporting and
  invalid-selection issues; full suite 36/36 after fixes.
- Test isolation correction: the first path regression test touched the local
  `.env` burst value. The user was informed; burst was set to the default 2x.
  The regression test now refuses writes outside its temporary directory.
- Task 4 complete: README updated, dead helper/imports removed, six tracked pyc
  files untracked without deleting local files, and ignore patterns corrected.
- Independent review: no Critical/Important regression. Reviewer found a lower
  matching midpoint could lose to the higher sample. Fixed in descending-y
  scan order after `test_choice_detector_prefers_midpoint_over_higher_answer`
  failed; final suite 40/40. Added overlapping-save and native query failure /
  handle-close tests in response to review gaps. No deferred minor findings.
- Final verification: all 40 unittest tests pass; syntax checks pass for all
  nine Python source/test files; GUI construction + queued F12 smoke passes with
  hooks disabled; actual read-only process query returns the correct executable.
- Remaining validation: live-game pixels, injected-input acceptance and CPS;
  simultaneous writers from different app processes are outside the single
  instance scope. Keep changes uncommitted as required by AGENTS.md.
