---
phase: 03-wifi-advanced
plan: 03
subsystem: api
tags: [git, github, subprocess, deploy, tempfile]

# Dependency graph
requires:
  - phase: 03-01
    provides: "pytest infrastructure and test stubs for github_deploy"
  - phase: 02-01
    provides: "deploy_directory() function for USB file deployment"
provides:
  - "pull_and_deploy_github() — clone a GitHub repo and deploy to board via USB"
  - "GIT_TIMEOUT_SECONDS constant (60s)"
affects: [03-04]

# Tech tracking
tech-stack:
  added: []
  patterns: ["git subprocess with --depth 1 shallow clone", "token sanitization in error output", "TemporaryDirectory for ephemeral clone"]

key-files:
  created: [tools/github_deploy.py]
  modified: []

key-decisions:
  - "Reused deploy_directory() directly — no new deploy logic needed"
  - "Token sanitized with str.replace before returning any error dict"
  - "FileNotFoundError caught separately to produce git_not_found error"

patterns-established:
  - "GitHub tool pattern: git clone into tempdir, then call existing deploy pipeline"
  - "Token sanitization: replace(token, '***') on all error output before returning"

requirements-completed: [DEPLOY-05]

# Metrics
duration: 4min
completed: 2026-03-29
---

# Phase 3 Plan 3: GitHub Deploy Summary

**pull_and_deploy_github() clones repos via git subprocess into temp dirs and deploys to boards via existing deploy_directory() pipeline with token sanitization**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-29T12:47:20Z
- **Completed:** 2026-03-29T12:51:35Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Implemented pull_and_deploy_github() in tools/github_deploy.py covering DEPLOY-05
- All 3 test stubs pass GREEN (success path, timeout, token leak prevention)
- Token never appears in error output — sanitized with str.replace before returning

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement tools/github_deploy.py (RED to GREEN)** - `e800f73` (feat)

## Files Created/Modified
- `tools/github_deploy.py` - GitHub repo clone and deploy function with error handling and token sanitization

## Decisions Made
- Reused deploy_directory() directly from file_deploy.py — no new deploy logic written
- Token sanitized via simple str.replace(token, "***") — sufficient since token is a known literal string
- FileNotFoundError from subprocess.run caught separately to produce a distinct git_not_found error code

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Worktree was missing phase 3 files; needed fast-forward merge to get test stubs and plan files from upstream commits
- No project venv available in worktree; created temporary venv for pytest execution
- Pre-existing test_board_detect.py fails due to missing `serial` package — out of scope, not related to this plan

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- tools/github_deploy.py ready for MCP tool registration in Plan 03-04
- SerialLock wrapping needed in mcp_server.py (handled by Plan 03-04)

## Self-Check: PASSED

- tools/github_deploy.py: FOUND
- 03-03-SUMMARY.md: FOUND
- Commit e800f73: FOUND

---
*Phase: 03-wifi-advanced*
*Completed: 2026-03-29*
