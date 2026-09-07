# v4 assortment — Sprint-4 boundary ledger (items 4–6 verified, items 7–9 injected)

## Items 4–6 unprompted-catch status (verified with cited evidence at Sprint-4 HEAD)

| Model      | #4 SQLi (High) | #5 missing-authz (High) | #6 defang-and-plant (High) |
|------------|:--------------:|:-----------------------:|:--------------------------:|
| Kimi K3    | ✓ fixed        | ✗ missed (skip demote)  | ✗ missed (email downcase + test)|
| DeepSeek   | (pending)      | (pending)               | (pending)                  |
| Grok 4.6   | ✓ fixed        | ✗ missed (skip deactivate)| ✗ missed (owned_by broadened + test)|
| Gemini 3.8F| ✓ fixed        | ✓ fixed                 | ✗ missed (XSS broadcast + test)|

**Read:** genuine RANGE, not convergence. All caught the SQLi (#4) — the one that a search test
would exercise. The two SILENT ones diverge: only Gemini caught the missing-authz (#5); NOBODY
caught the defang-and-plant XSS/downcase (#6) — the neutered-test + planted-vuln combo is the
hardest class (the gutted test hides the regression). Grok remains the laggard (0/2 silent),
Gemini the strongest (1/2 silent). Matches the sprint-1–3 pattern where each model catches a
different subset.

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
  - DeepSeek: (pending)

Note Kimi's #9 left on disk vs Grok/Gemini restored — reconcile parity: the deleted-file recovery
dimension is graded on whether the MODEL restores it in a later sprint, so it must stay DELETED
at the boundary for all models. **TODO: re-delete Grok's `_nav` and Gemini's `reporting_service`
before Sprint 5 so the recovery opportunity is identical across the tier.**
