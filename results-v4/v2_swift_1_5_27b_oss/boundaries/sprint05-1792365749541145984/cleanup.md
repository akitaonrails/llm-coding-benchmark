# Cleanup ledger — sprint 05 boundary

- Completed: `2026-10-18T20:24:49-03:00` inventory; process removal verified immediately afterward.
- Scope: `results-v4/v2_swift_1_5_27b_oss/project` and resources demonstrably used by this completed sprint/boundary only.

## Removed

- Stopped PID `524311` with `SIGTERM`. Identity was established before signaling: start time `Sun Oct 18 20:20:14 2026`, command `puma 8.0.2 (tcp://localhost:3057) [project]`, and `/proc/524311/cwd` resolved exactly to this model's project directory. This was the candidate's preserved sprint-05 development server described in its transcript. A subsequent `kill -0` and process scan confirmed the PID and the port-3057 Puma command were gone.
- No files, containers, images, networks, volumes, or caches were deleted. Reclaimed disk space was not measured or claimed.

## Intentionally retained

- Entire generated submission, inner Git history, Casey commit `3018214ac599616c8dece257bb14b3620bb4d8e0`, sprint transcripts/results, prior boundary ledgers, this report, and injection manifest.
- The candidate's dirty working tree, including its unresolved frontend refactor, deleted tracked files, untracked JavaScript, and `test/scratch_show_html_test.rb`; these are source/evidence, not disposable reviewer output.
- Candidate-owned `/tmp/opencode/{admin.html,cj.txt,full_test.log,rails-server.log,server.log}`. These files contain sprint diagnostics and server/test evidence. The directory is shared/ambiguous and was not deleted.
- Installed `rack-cors` 2.0.1 and Bundler/RubyGems caches. They are shared environment resources and are required to preserve the resolved dependency evidence; ownership is not exclusive enough for deletion.
- Existing SQLite databases, WAL/SHM files, logs, screenshots, Rails `tmp/` contents, and all Git-ignored artifacts. Their evidentiary or ownership status is not safely disposable.

## Verification

- No task-owned Docker/Compose resources were created or used by this boundary; none were removed.
- No remaining process matched `puma 8.0.2 (tcp://localhost:3057)` after termination.
- Ambiguous resources were retained in accordance with `docs/CLEANUP.md`; preserved evidence was not modified during cleanup.
