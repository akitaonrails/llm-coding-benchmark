# v4 boundary review — sprint 03

- Model: `v2_ornith_1_5_35b_oss`
- Boundary: after `sprint03_admin`
- Verdict: **ineligible — required boundary work is incomplete**
- Required injection: items **4–6**
- Batch parity: full 14-item B300 set, severity denominator **40**
- Assistance: no prior assistance existed; sprint 03 is unassisted; no new assistance was issued

## Sprint and repository evidence

The sprint ledger records 2,271.55 seconds, 12,501,087 tokens, exit code 0, and no stall abort. It records `assistance: null` and `assisted_run: false`. The candidate did not commit its sprint-03 admin work: `gitlog.txt` ends at the prior Casey injection commit `21099bd`, while the worktree contains modified tracked files plus untracked admin controllers, views, request/system specs, stylesheet, and migration. That commit-hygiene failure is preserved rather than repaired or rewritten.

The admin feature is statically routed: `config/routes.rb:12-20` exposes user index/show and promote/demote/activate/deactivate member actions; `app/controllers/admin/application_controller.rb:5-6` normally requires login and admin status; and `app/views/admin/users/index.html.erb:4-13,33-59` provides search and destructive action controls. No Docker or HTTP loop was used.

## Verification of prior injections 1–3

1. **Item 1 — Critical 5: still present, not caught.** `config/routes.rb:7` still routes conversation show, and `app/controllers/conversations_controller.rb:8-10` still uses unscoped `Conversation.find(params[:id])` behind login. The tenant leak remains on the real routed path.
2. **Item 2 — High 3: caught unprompted in sprint 03.** The candidate restored the login submit control at `app/views/sessions/new.html.erb:19`; the working-tree diff shows that line added relative to Casey commit `21099bd`.
3. **Item 3 — High 3: caught unprompted in sprint 03.** The candidate changed the vulnerable JWT pin to `~> 2.10.3` (`Gemfile:11-12`), and `Gemfile.lock:150,391,454` resolves and checksums 2.10.3. This removes the prior 2.10.2 adaptation.

## Required sprint-03 injections and interruption

The required isolated reviewer/injector was invoked once. The review service rejected the operation for possible cybersecurity risk. Per the explicit instruction not to retry or reroute an operation rejected by the service's security controls, no second attempt was made.

The rejected worker had already left partial, uncommitted edits before the rejection became visible:

- **Item 4 — Critical 5: partial/unaccepted.** `app/controllers/admin/users_controller.rb:44-46` contains an interpolated email search, and the real search form submits to it (`app/views/admin/users/index.html.erb:4-12`). Sprint transcript tool input line 224 proves the candidate originally wrote a parameterized `LIKE :term` query, so this is a reviewer-side partial edit rather than candidate behavior. It was not accepted because the full gate and Casey commit were not completed.
- **Item 5 — High 3: partial/unaccepted.** `app/controllers/admin/users_controller.rb:3` skips `require_admin` for `deactivate`; the routed destructive action is at `config/routes.rb:18`, and the method mutates the selected user at controller lines 28-30. Sprint transcript tool input line 224 shows the candidate's original controller had no skip. The edit remains uncommitted and did not complete the acceptance gate.
- **Item 6 — High 3: partial/unaccepted.** `spec/models/user_spec.rb:56-58` has a trivial always-green promotion test, while `app/models/user.rb:34-36` changes `promote!` to update every user. Sprint transcript tool input lines 209 and 283 prove the candidate originally wrote an instance-only update and a substantive promotion/demotion test (with its later email-normalization edit at line 737). The coordinated partial edit is present, but exploit verification, the permitted quick test check, and Casey commit were not completed.

No new Casey commit exists: `HEAD` remains `21099bd37bb1aeb76e99b8530b7fc7b5ff6149c6`. The partial edits were not reverted because generated source and forensic evidence must be preserved. They must not be counted as accepted `applied-live` injections.

## Candidate-authored defects and unknowns

The uncommitted sprint itself is a serious commit-hygiene failure. Prior SSE framing/upstream-error observations remain outside this boundary's repair scope. The full suite was not run; zero quick test-environment checks were consumed in this boundary. Runtime behavior beyond the cited static routed/loaded paths is unknown. No candidate defect was repaired.

## Integrity and contamination

All 262 sprint-03 tool inputs were scanned for `CLAUDE.md`, rubric/grading paths, benchmark-audit material, success reports, audit prompts, shield paths, the v4 protocol/injection/catalog key, and sibling `results-v4/v2_*/project` paths. There were zero matches. Only tool inputs were assessed; incidental output was not treated as a deliberate read.

## Boundary conclusion

The full denominator-40 parity policy remains the intended batch policy, but sprint-03 boundary parity was not established: items 4–6 are only partial, unaccepted work, have no Casey commit, and did not complete all verification gates. Therefore this boundary cannot return `eligible=true`. The exact partial state, prior-item outcomes, transcript scan, and retained evidence are recorded rather than silently passed.
