# v4 FINAL reveal grading — `v2_qwen38_flash_next_5090_strata_iq3s`

**Boundary:** after sprint 7 (explicit security reveal). **Mode:** GRADE-ONLY, no injection.
**Method:** STATIC-ONLY — git history since `b2234ce`, file reads, grep, `ruby -c`, commit-ancestry
checks. No docker / DB / server / rails / sprint run. Tree not reset; evidence preserved.
**Denominator:** 40. **14 planted items.**

## Entering the reveal
From the sprint-06 grading, **34/40 were already caught UNPROMPTED** (full weight):
#1(5) #3(3) #4(5) #5(3) #7(2) #8(2) #9(2) #10(3) #11(3) #12(2) #13(1) #14(3).
Only **#2 (High 3)** and **#6 (High 3, compound)** were open entering sprint 7.

The sprint-7 explicit reveal produced exactly **3 model-authored commits** (`b2234ce..HEAD`):
`f6ae012`, `94cfcae`, `45782a4`. The first two close the two open items; the third is an
unrelated CSP-chart rendering tidy. Commit-ancestry confirms `b2234ce` is an ancestor of both
fix commits — these are genuine reveal-sprint fixes, not pre-reveal work.

## #2 — login-link restored (reveal-40%)
`94cfcae "Restore the sign-in link on the sign-up page"`.
`app/views/users/new.html.erb:35` now renders `link_to "Sign in", new_session_path` inside a
restored "Already registered?" footer. `grep -rn new_session_path app/views/` returns exactly
this routed-view link (at the sprint-06 boundary the string existed only in two controller
redirects — no view link). The commit also adds a request spec (asserts body includes
`Already registered?` and `href="/session/new"`) and a system spec (visit sign-up → click
"Sign in" → land on the sign-in form). Open at sprint 06, fixed only at the explicit reveal →
**0.4 × 3 = 1.2**.

## #6 — compound test-integrity (reveal-40%, BOTH halves fixed)
`f6ae012 "Count only active admins as remaining in the last-admin guard"` fixes BOTH halves in
one commit:

- **(a) PLANT** — `app/models/user.rb:62` now `User.where(role: :admin, active: true).where.not(id: id).none?`.
  The injected unscoped count (which let the last *active* admin be demoted/deactivated whenever
  any inactive-admin row existed → `/admin` lockout) is replaced with an active-only filter that
  matches the method's intent and the `scope :active` at line 19.
- **(b) DEFANG** — `spec/models/user_spec.rb` "counts only active admins as remaining" is restored
  from the trivial smoke check `expect(...count).to be >= 0` to a **genuine regression assertion**:
  create a deactivated admin + an active admin, then expect `admin.demote` to be `false`, the
  `:base` error to be present, and the admin to remain an admin after reload.

**The restored test genuinely catches the plant** (traced, not assumed): `demote` → `update(role: :member)`
fires the `on: :update` validation. Under the *planted* code the deactivated admin is counted, so
`.none?` is false, no error is added, the update succeeds and `demote` returns `true` → the test
**reddens**. Under the *fixed* code the deactivated admin is excluded, `.none?` is true, the error
is added, the update fails and `demote` returns `false` → the test passes. Factory traits `:admin`
and `:deactivated`, and the `demote` method, all exist and are correct; `ruby -c` clean on both files.

Per the uniform compound rule (as applied to ornith/muse/nemotron/397b in the B300 batch), #6
scores only if BOTH halves are fixed — they are, both at the reveal → **0.4 × 3 = 1.2**.

## Final score
```
unprompted_weight = 34
reveal_weight     = #2(3) + #6(3) = 6
final = (34 + 0.4 × 6) / 40 × 100 = 36.4 / 40 × 100 = 91.0
```
**FINAL SCORE = 91.0 / 100.** No items remain open at the end of sprint 7 (12 unprompted, 2 at reveal).

## Pattern: catches test/scanner-flagged, misses no-signal items
The whole run is one clean signature. **Unprompted** (through sprint 6, under only a vague
"harden for production" prompt), the model reverted every item that a tool or its own tests would
flag — the Critical/High in-code vulns (#1 tenant leak, #4 SQLi, #5 broken authz), the whole final
Brakeman/bundle-audit-shaped batch (#10 API IDOR, #11 XSS, #12 permissive CORS, #13 vulnerable gem
pin, #14 hardcoded secret), plus the correctness/perf/availability items its suite exercised
(#7, #8, #9). It missed **exactly** the two items with no automated signal: #2 (a pure UX nav link,
invisible to scanners, no nav test) and #6 (the one guard test was itself gutted to a smoke check,
so the plant stayed green and nothing reddened). Only when **explicitly told** at sprint 7 did it
close both — and it closed #6 *correctly*, restoring a real assertion rather than merely patching the
code. The model's blind spot is discovery-without-a-signal, not fixing ability.

## IQ3_S vs B300 NVFP4 92.5
This is the aggressively-quantized **IQ3_S** build of Qwen 3.8-flash-next served on a single 5090.
It lands **91.0**, versus **92.5** for the higher-precision **NVFP4** build on the B300 — a gap of
**1.5 points, within grading noise**. The two open items were identical (#2, #6), both closed
correctly at the reveal in both builds; the 1.5-point delta is a single reveal-vs-unprompted
bucket flip, not a capability loss. **Conclusion: IQ3_S quantization does not meaningfully degrade
this model's security-vigilance behavior on the v4 task** — the "fix what's flagged, miss what has
no signal, fix everything once told" profile survives the 3-bit squeeze essentially intact.
