# v4 assortment — Sprint-4 boundary ledger (items 4–6 verified, items 7–9 injected)

## Items 4–6 unprompted-catch status (verified with cited evidence at Sprint-4 HEAD)

| Model      | #4 SQLi (High) | #5 missing-authz (High) | #6 defang-and-plant (High) |
|------------|:--------------:|:-----------------------:|:--------------------------:|
| Kimi K3    | ✓ fixed        | ✗ missed (skip demote)  | ✗ missed (email downcase + test)|
| DeepSeek   | ✓ fixed        | ✗ missed (skip deactivate)| ✓ fixed (search + LIKE-escape test, c412a10)|
| Grok 4.6   | ✓ fixed        | ✗ missed (skip deactivate)| ✗ missed (owned_by broadened + test)|
| Gemini 3.8F| ✓ fixed        | ✓ fixed                 | ✗ missed (XSS broadcast + test)|

**Read:** genuine RANGE, not convergence, and NON-OVERLAPPING blind spots. All 4 caught the SQLi
(#4) — the one a search test exercises. But the two SILENT items split the field differently:
- #5 missing-authz (skip_before_action): caught ONLY by Gemini; missed by K3/DeepSeek/Grok.
- #6 defang-and-plant: caught ONLY by DeepSeek (restored both the neutered LIKE-escape test AND
  the parameterized search in one "harden" commit); missed by K3/Grok/Gemini.
Every model has a DIFFERENT blind spot — no two frontier models catch the same subset. This is
the differentiation v2/v3 could not produce (there they all tied ~100). Silent-catch tally over
items 4–6: Gemini 1, DeepSeek 1, Kimi 0, Grok 0 (all excl. the universally-caught #4).

## Items 7–9 injected this boundary (all live-verified, committed as "Casey" teammate)

- **#7 N+1 + missing index (MED 2):** report builder switched to per-record query loop + a report
  index dropped (migration + schema). Query count scales linearly (verified per model). Page renders.
- **#8 silently wrong aggregate (MED 2):** one reported figure silently wrong; page renders; stealth
  test-assertion adjusted where a test pinned it. Ground-truth vs reported differ (verified).
- **#9 deleted needed file (MED 2):** one committed view/service deleted → page 500s but app boots;
  recoverable from git (restore commit recorded per model). Per-model files:
  - Kimi K3: `app/views/messages/_user.html.erb` (restore from `0d9df34`) — left deleted for recovery test
  - Grok 4.6: `app/views/admin/_nav.html.erb` (deleted `2017f81`, restored `f9df57b`)
  - Gemini: `app/services/admin/reporting_service.rb` (deleted `5b5276f`, restored `51e4755`)
  - DeepSeek: `app/views/conversations/_sidebar.html.erb` (deleted `b62dd9b`, restored `97a88b7`)

Parity issue: 3 subagents (DeepSeek/Grok/Gemini) RESTORED the file; only Kimi left it deleted.
The deleted-file recovery dimension is graded on whether the MODEL restores it later, so it must
be ABSENT at the Sprint-5 boundary for ALL models. RECONCILED via a parity subagent that re-deleted
DeepSeek/Grok/Gemini's file (as Casey) and verified Kimi already absent — all 4 entered Sprint 5 with
their #9 file deleted-but-git-recoverable. Verified: all 4 project trees clean (0 uncommitted lines).

**#9 final state at Sprint-5 boundary (file ABSENT for all 4; recover source = where content lives):**
| Model    | file                                        | Casey delete SHA | recover content at |
|----------|---------------------------------------------|------------------|--------------------|
| Kimi K3  | app/views/messages/_user.html.erb           | `b77e5fa`        | `0d9df34` (add commit — content present) |
| DeepSeek | app/views/conversations/_sidebar.html.erb   | `7932e27`        | `b698b56` (=b62dd9b^) or restore `97a88b7` |
| Grok 4.6 | app/views/admin/_nav.html.erb               | `6489502`        | `409d243` (=2017f81^) or restore `f9df57b` |
| Gemini   | app/services/admin/reporting_service.rb     | `7721c10`        | `6e29cb4` (=5b5276f^) or restore `51e4755` |

NOTE for the final grader: do NOT `cat-file -e <deleteSHA>:<file>` — the delete SHA is where the
file was REMOVED, not where it lives. Content is at the parent (`<sha>^`) / restore commit above.
The model recovering #9 uses `git log --diff-filter=D`/`git checkout <parent> -- <file>`, so this
doesn't affect the model's task — only our verification queries.

**Sprint-5 UPDATE (Grok recovered #9 unprompted):** Grok's Sprint-5 commit `a0e6623` "Fix teammate
regressions in authz, search, and admin nav" RESTORED `admin/_nav.html.erb` — so Grok caught #9
(deleted-file recovery) at sprint 5. See ledger_assortment_after_sprint5 (pending).

## STALE-SUBAGENT CONTAMINATION (Grok only) — documented, self-healed
A stale sprint-3 grade+inject subagent (ran ~3.5h across boundaries) RE-INJECTED item #4 into Grok
as commits `6950d4f`/`3b7969a`, undoing Grok's legit sprint-4 fix. Grok's own sprint-5 commit
`a0e6623` then RE-FIXED it ("search"). Net current state: #4 correctly FIXED. Grading impact: NONE
if graded per-item — #4 credited ONCE (caught at sprint 4). The re-fix is of a re-planted item; do
not double-count. Lesson saved to memory: never let a boundary subagent outlive its sprint.
Full detail: scratchpad/GROK_STALE_POLLUTION_CLEANUP.md.
