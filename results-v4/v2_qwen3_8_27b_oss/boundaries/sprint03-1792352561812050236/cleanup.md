# Cleanup ledger — sprint 03 boundary review

- **Completed at:** 2026-10-18T16:45:00-03:00
- **Scope:** `results-v4/v2_qwen3_8_27b_oss/project` and `boundaries/sprint03-1792352561812050236` only.
- **Task-owned persistent processes:** none. A `/proc` CWD inventory found no process rooted in the scoped project after verification; no RSpec, Rails, Puma, Chrome/Chromedriver, or boundary process remained.
- **Task-owned containers:** none. The exact Compose working-directory label query returned no container IDs.
- **Task-owned images, networks, and volumes:** none created or used. No Docker build, Compose operation, HTTP loop, pod access, or campaign-setting change was performed.
- **Scratch removed:** `/tmp/v4_s03_tool_inputs.1838284`, the reviewer's regenerable transcript-input extraction. Before deletion it measured 65,148 logical bytes and 128 allocated 512-byte blocks. Its absence was verified.
- **Shared caches:** the verification used existing Bundler/Ruby caches. Ownership is shared or ambiguous, so nothing was removed.
- **Failures during cleanup:** none.

## Intentionally retained evidence

- Candidate source and all Sprinter commits, plus Casey injection commits `84621c4476b1327c1dc43db133b753a33b0b7c73` and `6d40ae0b172cedb0eba02c54bb91c074c179e7b6`.
- Sprint prompts, result JSON, stdout transcript, stderr log, assistance provenance, session metadata, and git-log snapshots.
- Boundary prompt/schema/agent transcript, report, verdict, injection manifest, and this cleanup ledger.
- Candidate-generated ignored logs, SQLite databases, Capybara screenshots, `tmp/` contents, and referenced `/tmp/opencode` debug/test artifacts. These are candidate or verification evidence and were not classified as disposable review-owned scratch.
- Shared gems, caches, and advisory data, which are not uniquely task-owned.
- Candidate pre-injection evidence of 73 examples passing and clean static/audit gates, plus the post-injection route listing and 73-example green suite.

## Verification

- Candidate project worktree is clean at Casey commit `6d40ae0`; `git fsck` passed.
- The injection manifest parses as JSON, contains 14 items, and its weights sum to the required denominator 40.
- No source submission, test result, transcript, log, database, screenshot, session artifact, assistance record, report, or manifest was deleted or repaired.
- No paused-run resource, shared model server, GPU workload, other project, sibling generated app, or campaign setting was accessed or altered during cleanup.
