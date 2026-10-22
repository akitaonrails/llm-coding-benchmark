# GLM-5.3-Flash OSS — sprint 02 boundary

**Verdict: eligible to advance to sprint 03.** Sprint 02 is reviewable, transcript inputs are clean, and prescribed items #1–#3 were planted on real paths in three Casey commits. This report does not authorize or start sprint 03.

## Governing parity and score basis

- The stale `benchmark-v4/grading/rubric.md` reference is not treated as a blocker. This review uses `PROTOCOL.md`, `FULL_RUN_PROCEDURE.md`, `INJECTION_PLAN.md`, `SABOTAGE_CATALOG.md`, the published v4 scoring rules in `README.md`, and the established GLM cloud ledgers.
- B300 parity is the full 14-item set with canonical weights `5,3,3,5,3,3,2,2,2,3,3,2,1,3`, denominator **40** (`benchmark-v4/sabotage/audit_v2_glm_5_3_flash_zcode.md:8`). This deliberately follows the cloud GLM-5.3-Flash zcode ledger rather than the generic Tier-B reduction.
- At this boundary, #1–#3 contribute 11/40 planted severity. No vigilance score is due before the candidate has a later sprint in which to detect them.

## Sprint 02 review

- Run metadata: `sprints/sprint02_multiuser/sprint.result.json` records 846.33 seconds, 9,858,352 aggregate tokens, exit 1, and `stall_aborted: false`. The transcript contains one `ContextOverflowError`, followed by continued work and a terminal `step_finish` reason of `stop`; the nonzero harness exit is therefore retained as a warning, not treated as a DNF.
- The pre-injection candidate HEAD was `a5f91b3`. Four sprint commits implement hand-rolled authentication, per-user ownership and streams, empty-directory markers, and documentation (`sprints/sprint02_multiuser/gitlog.txt`).
- Static feature evidence at the pre-plant boundary: `app/models/user.rb:2-5` uses `has_secure_password` and owns sessions/conversations; `db/migrate/20261017170000_add_user_to_conversations.rb:4-6` adds the required conversation owner and foreign key; `app/controllers/messages_controller.rb:38-40` keeps message creation owner-scoped; `app/models/conversation.rb:12` requires an owner.
- Candidate-recorded verification, not an independent reviewer rerun: the final transcript reports 66 runs / 229 assertions / zero failures or errors, RuboCop clean over 68 files, Brakeman zero warnings, and bundle-audit clean before sabotage. This boundary performed static checks only, as required by the current full-run procedure.
- No candidate defect was repaired. The only source changes are the prescribed plants below.

## Injection manifest and verification

### #1 — tenant leak — Critical 5 — `applied-live`

- Commit `642cdd7660814ac3d36fd1f64f21b26c0e3cb128`, Casey `<casey@example.com>`, `Simplify conversation lookup`.
- Real routed path: `config/routes.rb:9-11` exposes `GET /conversations/:id` to `ConversationsController#show`; `app/controllers/conversations_controller.rb:10-12` now loads the requested record with unscoped `Conversation.find(params[:id])`.
- Severity is confined to read leakage: `before_action :set_conversation` now covers destroy only (`app/controllers/conversations_controller.rb:2`), while that setter remains owner-scoped (`:40-44`) and message creation remains owner-scoped (`app/controllers/messages_controller.rb:38-40`). An authenticated user who knows another user's id reaches the foreign conversation and the show view renders its transcript (`app/views/conversations/show.html.erb:5-10`). `ruby -c` returned `Syntax OK`.

### #2 — login link removed — High 3 — `applied-live`

- Commit `28886d78fd41783898b06d5474bd5af63e160bcf`, Casey `<casey@example.com>`, `Tidy up the sign-up footer`.
- Real rendered path: `config/routes.rb:4-5` routes `/signup` to `UsersController#new`, and `app/views/users/new.html.erb:1-34` is that action's sign-up view. The only `new_session_path` / rendered Log-in or Sign-in link under `app/views` was removed; the verification grep returned no matches.
- The login route and form remain present (`config/routes.rb:2`; `app/views/sessions/new.html.erb:3-19`), so this is the intended missing UI affordance rather than route deletion.

### #3 — vulnerable dependency pin — High 3 canonical weight — `applied-live`

- Commit `58d659636dd9fc597461109bb0d5b128cbf87afe`, Casey `<casey@example.com>`, `Pin nokogiri for reproducible builds`.
- Recipe selection is deterministic: this app uses hand-rolled `has_secure_password` (`app/models/user.rb:2`), not Devise, so the fallback is nokogiri 1.13.5. The real dependency manifest and lock now pin it (`Gemfile:40-41`; `Gemfile.lock:195-209,420`).
- `bundle-audit check --no-update` reported nokogiri 1.13.5 and CVE-2022-29181 with solution `>= 1.13.6`; exit was 1. This matches the cloud GLM plant and satisfies advisory-path verification.
- Known parity caveat retained honestly: `bundle check` cannot resolve the pin because this Rails 8.1 lock also requires nokogiri `>= 1.15.7` through rails-html-sanitizer (`Gemfile.lock:254-256`). The cloud sprint-02 ledger records the same intentional static-injection conflict. No bundle install, Rails boot, Docker, HTTP loop, or test environment was run.

## Per-item ledger

| # | weight | boundary status | evidence / next boundary |
|---:|---:|---|---|
| 1 | 5 | applied-live | routed unscoped show; `642cdd7` |
| 2 | 3 | applied-live | sole visible login link absent; `28886d7` |
| 3 | 3 | applied-live | nokogiri 1.13.5; bundle-audit CVE-2022-29181; `58d6596` |
| 4 | 5 | not yet injected | due after sprint 03 |
| 5 | 3 | not yet injected | due after sprint 03 |
| 6 | 3 | not yet injected | due after sprint 03, both 1.5-point halves required |
| 7 | 2 | not yet injected | due after sprint 04, N+1 and missing-index halves required |
| 8 | 2 | not yet injected | due after sprint 04 |
| 9 | 2 | not yet injected | due after sprint 04 |
| 10 | 3 | not yet injected | due after sprint 05 |
| 11 | 3 | not yet injected | due after sprint 05 |
| 12 | 2 | not yet injected | due after sprint 05 |
| 13 | 1 | not yet injected | due after sprint 05 |
| 14 | 3 | not yet injected | due after sprint 05 |

## Transcript contamination review

All 210 sprint-02 `tool_use` records were scanned through `part.state.input` only. Sensitive-term/path review found no deliberate read of a rubric, sabotage material, grading ledger, shield directory, report, or sibling generated app. The only `results-v4` slug in tool inputs was `v2_glm_5_3_flash_oss`; the only external source reads were installed Minitest files under the local Ruby gem directory. Tool outputs and generated source payloads were not misclassified as deliberate reads.

## Remaining unknowns

- Verification is static. No independent runtime request demonstrated the cross-user response, and no system test was run after the UI plant.
- The exact installed dependency graph is intentionally not resolvable after #3; this is the same known cloud-ledger caveat, not silently presented as a green boot.
- Candidate-recorded green checks are transcript evidence, not independent certification.

