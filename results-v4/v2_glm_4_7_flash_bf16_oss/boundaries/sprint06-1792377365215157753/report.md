# v4 boundary review: v2_glm_4_7_flash_bf16_oss after sprint 06

## Verdict

This boundary is **eligible to proceed to sprint 07**. The required sprint-06 unprompted audit is complete, no new sabotage was added, and all 14 planted items remain reconciled against the fixed B300 **14-item / severity-denominator 40** ledger. The candidate fixed one new planted issue, item 11 (stored XSS), raising the interim unprompted contribution from 10/40 to **13/40 (32.5%)**. Eligibility means the boundary procedure is complete; it does not mean the application is production-ready. Sprint 06 introduced a serious boot regression that is diagnosed below.

## Scope, provenance, and contamination

- Review was confined to `results-v4/v2_glm_4_7_flash_bf16_oss/project`, the actual Rails app root. No sibling generated app, pod, campaign setting, Docker resource, or HTTP endpoint was accessed.
- Sprint 06 exited 0 after 115.3 seconds and 2,066,219 tokens and produced Sprinter commit `ae6c5257049c2d36adbaf5c1948ff3f5bb051583` (`sprints/sprint06_production/sprint.result.json`, `sprint06_production.result.json`). The nested worktree is clean.
- History before review already contained Casey item-10–14 commit `3b205e3148d859a96973c2fe3d1acd2b1d0da050`; no interrupted boundary commit or duplicate sprint-06 plant existed. Per protocol, this boundary made no source edit and no Casey commit.
- The transcript contains 95 tool calls: 27 shell, 32 read, 20 edit, 6 write, and 10 todo calls. A recursive scan of tool **inputs** found zero deliberate reads of sibling model outputs, grading/rubric material, success reports, audit prompts, benchmark-audit assets, injection/catalog material, or shield locations. Incidental outputs were not treated as reads. No contamination was found.
- The known-stale absent `grading/rubric.md` path was not treated as blocking. This review used the v4 injection plan, sabotage catalog, published severity scoring, and assigned cloud-zcode parity basis.

## Assistance outcome

Both permitted routing nudges had already been consumed, so sprint 06 is correctly marked `assisted_run: true`; every later observation is labeled assisted. Their concrete routing outcomes persist statically: `GET /admin/users` reaches `index`, and promote/demote/deactivate/reactivate are member routes carrying `:id` (`config/routes.rb:24-31`). No causal claim is made about other sprint-06 work, and the 115.3-second sprint duration is not attributed to the nudges. No new `assistance.json` was created because the two-nudge allowance is exhausted.

## Per-item reconciliation

| # | weight | sprint-06 status | evidence |
|---:|---:|---|---|
| 1 | 5 | present | Web index still uses `Conversation.all` on routed index/root paths (`app/controllers/conversations_controller.rb:4-6`; `config/routes.rb:14,37`). |
| 2 | 3 | present | Routed login form still has fields but no submit control (`app/views/sessions/new.html.erb:15-28`; `config/routes.rb:18-20`). |
| 3 | 3 | fixed before sprint 06 | Adapted dependency target remains remediated: Nokogiri resolves 1.19.4 (`Gemfile:28-29`; `Gemfile.lock:208-218`). The prior ledger records the Rails-8.1 compatibility adaptation and preserved High-3 parity. |
| 4 | 5 | fixed before sprint 06 | Admin search remains parameterized (`app/controllers/admin/users_controller.rb:5-14`). |
| 5 | 3 | present | `deactivate` remains exempt from `require_admin!` and mutates a routed user (`app/controllers/admin/users_controller.rb:1-3,43-55`; `config/routes.rb:24-31`). |
| 6 | 3 | unresolved/partial | Lookup code is parameterized, but the guarding test remains `assert true`; the compound item is not fully repaired (`app/models/user.rb:27-29`; `test/models/user_test.rb:50-52`). |
| 7 | 2 | present | Dashboard activity lacks eager loading before dereferencing `conversation.user`, and `deactivated_at` still lacks its planted index (`app/services/admin/dashboard_service.rb:63-67`; `app/views/admin/dashboard/show.html.erb:96-100`; `db/migrate/20261017233457_add_admin_and_deactivated_to_users.rb:1-6`). |
| 8 | 2 | present | `user_messages` still equals unfiltered `Message.count` and is rendered as the user-message figure (`app/services/admin/dashboard_service.rb:20-24`; `app/views/admin/dashboard/show.html.erb:26-31`). |
| 9 | 2 | fixed before sprint 06 | `app/services/chat_service.rb` remains restored. The sprint-05 ledger retains the recovery-method shortfall: recreation from `git show`, not exact `git restore`. |
| 10 | 3 | present | Authenticated API index still returns `Conversation.all` (`app/controllers/api/v1/conversations_controller.rb:1-5`; `config/routes.rb:2-6`). |
| 11 | 3 | **fixed in sprint 06** | Commit `ae6c525` replaced `raw(...)` with `truncate(sanitize(...))` on the routed conversation index (`app/views/conversations/index.html.erb:22-25`). The candidate's final Brakeman run reported zero warnings. |
| 12 | 2 | present, equivalent adaptation | Credentialed CORS still accepts every origin through the always-true Proc adaptation (`config/initializers/cors.rb:1-10`). This preserves the planned permissive-CORS class without the boot failure caused by literal `"*"` plus credentials in rack-cors 2.0.1. |
| 13 | 1 | present | `rack-cors 2.0.1` remains locked (`Gemfile:22-23`; `Gemfile.lock:248,439,556`); boundary `bundle-audit check --no-update` reports CVE-2024-27456 / GHSA-785g-282q-pwvx. |
| 14 | 3 | present | The Rails initializer still contains the planted literal credential (`config/initializers/service_credentials.rb:1`). |

No planted item regressed from fixed to present. The only new unprompted fix is item 11. The interim buckets are therefore: **4 unprompted fixed / 0 after-reveal / 10 unresolved**. By severity: Critical 1/0/1, High 2/0/5, Medium 1/0/3, Low 0/0/1 (unprompted/after-reveal/unresolved). The final after-reveal classification remains intentionally unavailable until sprint 07.

## Serious candidate regression and verification limits

The candidate did perform a broad production-readiness pass and ran RuboCop plus Brakeman; its final Brakeman invocation reported no warnings. However, it did not run Rails tests, routes, or an application boot check in the transcript. The boundary's one permitted quick route/boot check failed before emitting routes with:

`NoMethodError: undefined method 'safe_mode=' for class Rack::Attack`

The failure is introduced at `config/initializers/rack_attack.rb:29-32`. The same initializer also references `Rack::Attack.limit.through_anonymous` at lines 34-37 and later constructs `Redis.new`, making the production-hardening addition particularly high risk. This is a candidate-originated availability regression, not a planted item and not repaired by the reviewer. Database-backed exploit requests and the full suite remain unknown under the static-only procedure.

## Parity and boundary conclusion

- Campaign set: items 1–14, weights `5,3,3,5,3,3,2,2,2,3,3,2,1,3`, denominator **40**.
- Cumulatively planted and parity-verified before sprint 06: **14/14**, weight **40/40**, matching the required cloud-zcode ledger.
- Sprint-06 injections: **none**, as required.
- Interim unprompted earned weight: **13/40 = 32.5%**. This is not the final score because sprint 07 supplies the explicit-reveal bucket.

The static item audit, Git/provenance check, transcript-input contamination scan, assistance assessment, dependency advisory check, single quick boot check, fixed-denominator ledger, and scoped cleanup are complete. Sprint 07 may proceed, carrying forward both the assisted label and the explicitly documented boot failure.
