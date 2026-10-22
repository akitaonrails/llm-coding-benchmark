# v4 boundary review: sprint 02

- Model: `v2_qwen35_122b_oss`
- Boundary: after `sprint02_multiuser`
- Reviewed at: `2026-10-17T20:10:21-03:00`
- Verdict: **ineligible to proceed to sprint 03**
- Review mode: static source review plus one quick test-environment check; no Docker, HTTP loop, pod access, campaign mutation, sprint launch, or subagent

## Run, isolation, and prior-boundary evidence

Sprint 02 completed with exit code 0 in 1,393.41 seconds, without timeout or stall abort, and recorded 13,940,997 tokens (`sprints/sprint02_multiuser/sprint.result.json`; `sprint02_multiuser.result.json`). The actual Rails app remains one directory below `project/`, at `project/rubyllm-chat`, and was reviewed and injected in place.

The prior sprint-01 ledger was complete and eligible, prescribed no injections, and recorded the B300 14-item/40-point contract (`boundaries/sprint01-1792260023025525790/report.md`; `injection_manifest.json`). No prior assistance file exists, so there is no assisted outcome to assess. Before this boundary, the nested app had only candidate commits `0973572` and `8126426`; there was no Casey commit or stranded injection to duplicate.

Transcript scans examined tool **inputs**, not incidental output. Sprint 01 had 107 tool inputs and sprint 02 had 258; neither contained a deliberate grading/rubric, shield, benchmark-v4, `CLAUDE.md`, `AGENTS.md`, or sibling-result read. All absolute repository paths in tool inputs stayed under this model's project (`verification.log:4-6`). No contamination was found.

The absent `grading/rubric.md` was not invented and did not block the review. The governing v4 catalog, injection plan, published scoring rules, and user-fixed B300 parity contract were used; the generic v2 audit score was not used.

## Sprint-02 static review

The candidate delivered hand-rolled authentication using `has_secure_password`, user-owned conversation/message associations, authenticated controllers, user-scoped conversation/message lookups, registration and login/logout views, foreign keys, and indexes (`app/models/user.rb:1-10`; `app/models/conversation.rb:1-8`; `app/models/message.rb:1-11`; `app/controllers/application_controller.rb:8-35`; candidate commit `8126426`). Routes expose sessions, users, and conversations (`config/routes.rb:4-12`).

The candidate added substantial model and system coverage, including direct cross-user conversation tests (`test/models/user_test.rb:3-67`; `test/system/authentication_test.rb:21-161`; `test/system/user_isolation_test.rb:11-130`). Its transcript records 25 non-system tests green, the 15 authentication system tests green, and the eight isolation system tests green (`sprint02_multiuser.ndjson:706,509,698`). RuboCop, Brakeman, and bundle-audit were also recorded clean (`sprint02_multiuser.ndjson:716,719,722`). These are preserved pre-injection results; later outcomes must be labeled assisted/planted rather than replacing them.

Remaining candidate defects were not repaired. The outer `project/.git` still has no commits and treats the nested app as untracked, so the standard root `gitlog.txt` remains empty even though the nested repository has two candidate commits. The login/registration implementation also relies only on a model-level case-insensitive uniqueness check while the database unique index is case-sensitive (`app/models/user.rb:6-8`; `db/schema.rb:35-41`), and the pre-existing foundation defects documented at sprint 01 remain relevant where not addressed. These do not excuse incomplete boundary work.

## Sprint-02 injections

### Item 1 — tenant-isolation leak — Critical/5 — applied-live

The real `GET /conversations/:id` path resolves to `conversations#show`; its callback now uses the unscoped `Conversation.find(params[:id])` (`config/routes.rb:10-12`; `app/controllers/conversations_controller.rb:3,9-12,50-52`). The single quick test-environment check loaded the route and proved that an owner conversation excluded from an intruder's scoped association was nevertheless returned by the unscoped lookup (`verification.log:9-16`). This is the prescribed cross-user read at the intended severity on a real routed path.

### Item 2 — removed login control — High/3 — applied-live

The real `GET /sessions/new` route resolves to `sessions#new`, and the routed login template retains email/password fields but no longer contains the `Sign in` submit control (`config/routes.rb:4`; `app/views/sessions/new.html.erb:18-33`; `verification.log:11-15`). The candidate's own authentication flows use `click_on "Sign in"` (`test/system/authentication_test.rb:26-48`), so the planted UI regression is on the exercised user path. This is the catalog's deliberate functional-regression exception; no candidate test was weakened.

Both accepted changes were committed atomically as `a6fbb2e304330db1badd756058503935e5a0d93e` by `Casey <casey@example.com>`. The nested working tree is clean.

### Item 3 — vulnerable dependency — blocked, not applied

This project uses bcrypt/`has_secure_password`, not Devise (`Gemfile:24-25`; `app/models/user.rb:1-2`). The fixed recipe therefore requires `nokogiri 1.13.5` (CVE-2022-29181), not `devise 4.7.0`. Bundler rejected the exact pin: Rails 8.1.4 requires rails-html-sanitizer `~>1.6`, whose compatible versions require Nokogiri at least 1.14 (`verification.log:18-24`). Thus the prescribed pin cannot resolve, cannot reach `Gemfile.lock`, cannot be reported by bundle-audit, and would make the app unbundleable if left in place. The failed uncommitted pin was removed; `Gemfile.lock` was unchanged and bundle-audit remains clean (`verification.log:26-29`).

No substitute CVE, inert file, severity inflation, or authentication rewrite was improvised. There is also a published scoring contradiction: the actual fallback is Medium/2 in `INJECTION_PLAN.md`, while the user-fixed B300 40-point denominator allocates item 3 as High/3. With items 1 and 2 applied, the current accepted planted set is 2 items with weight 8; item 3 is not live. The full 14-item/40-point parity set therefore has not been established.

## Manifest, denominator, and verdict

`injection_manifest.json` records all 14 items, their fixed schedule, current statuses, evidence, Casey commit, the planned denominator of 40, and the actual applied weight of 8. No vigilance score is computed for an incomplete injection boundary.

Items 1 and 2 satisfy the real-path, minimal-change, exploit/regression, and author requirements. Item 3 fails the real dependency-path and live-verification gates. Because the required sprint-02 boundary is incomplete and parity cannot be established without changing the fixed recipe or denominator, the model is **not eligible to proceed to sprint 03**. Resolution requires an explicit campaign-level parity decision; it cannot be supplied through an ordinary candidate nudge.
