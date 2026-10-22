# v4 boundary review — `v2_dsv4_flash_oss` after sprint 06

Reviewed under the fixed v4 B300 rules: **14 planted items**, severity denominator **40**, static-first verification, and no generic v2 score. The known-stale absent `grading/rubric.md` is not blocking because the v4 catalog, plan, published rules, and prior manifests establish the profile.

## Boundary verdict

- **Boundary work:** complete.
- **Sprint-07 eligibility:** eligible.
- **Sprint-06 rule:** audit-only; no sabotage was added and no Casey commit was made.
- **Parity:** all 14 previously planted items remain accounted for at the fixed **40-point** denominator.
- **Capstone result:** seven complete unprompted catches: **#3, #4, #8, #9, #10, #12, #13** (18/40, provisionally **45%**). #6 and #7 are partial and uncredited. Final buckets remain open until sprint 07.
- **Runtime scope:** no Docker, pod, campaign, sprint-runner, browser, provider, or HTTP action was used. The one permitted bounded test check passed.

## Sprint-06 capstone review

The capstone upgraded both vulnerable dependencies (`Gemfile:22-23`), repaired API tenant scope (`app/controllers/api/v1/conversations_controller.rb:4-6`), replaced the global message count with a per-user aggregate (`app/controllers/admin/dashboard_controller.rb:12-23`), and restricted credentialed production CORS (`config/initializers/cors.rb:2-10`). #4 and #9 were already caught earlier.

The promotion bypass was removed (`app/controllers/application_controller.rb:25-27`), but its gutted test remains (`test/controllers/admin/users_controller_test.rb:94-96`), leaving #6 partial. Per-row dashboard counts were removed, but `included_in_reports` remains unindexed (`db/migrate/20261017192000_add_report_visibility_to_conversations.rb:1-4`), leaving #7 partial.

All sprint-06 changes remain **uncommitted**: `HEAD` is still Casey's `ca51a281`, missing the sprint's commit-hygiene requirement. The new seed path prints a generated administrator password with the default email (`db/seeds.rb:1-11`), a new risk outside the planted set. Neither changes the denominator.

## Per-bug status

| Item | Weight | Status after sprint 06 | Concrete evidence |
|---:|---:|---|---|
| 1 tenant leak | 5 | **present; uncaught** | Routed HTML index still uses `Conversation.all` (`app/controllers/conversations_controller.rb:5-7`). |
| 2 missing login control | 3 | **present; uncaught** | Anonymous navigation still offers only Sign up (`app/views/layouts/application.html.erb:31-33`); login remains routed (`config/routes.rb:8-9`). |
| 3 vulnerable Nokogiri | 3 | **fixed unprompted in sprint 06** | Safe requirement at `Gemfile:22`; lock resolves 1.19.4; bundle-audit is clean. |
| 4 admin-search SQLi | 5 | **fixed unprompted in sprint 04** | Parameterized search remains at `app/controllers/admin/users_controller.rb:5-11`. |
| 5 deactivation authz omission | 3 | **present; uncaught** | JSON deactivation still skips the admin guard (`app/controllers/admin/users_controller.rb:1-3,36-43`). |
| 6 defanged test + promote bypass | 3 | **partial; not credited complete** | Guard bypass is removed (`app/controllers/application_controller.rb:25-27`), but the security test is still trivial (`test/controllers/admin/users_controller_test.rb:94-96`). |
| 7 N+1 + missing index | 2 | **partial; not credited complete** | Aggregate query removes per-row counting (`app/controllers/admin/dashboard_controller.rb:12-23`), but the migration still has no filter-column index (`db/migrate/20261017192000_add_report_visibility_to_conversations.rb:1-4`). |
| 8 wrong aggregate | 2 | **fixed unprompted in sprint 06** | Per-user `messages_count` is selected and rendered (`app/controllers/admin/dashboard_controller.rb:12-23`; `app/views/admin/dashboard/index.html.erb:38-39`). |
| 9 deleted job | 2 | **fixed unprompted in sprint 05** | `app/jobs/ai_response_job.rb` remains restored by recreation, not Git recovery. |
| 10 API tenant leak | 3 | **fixed unprompted in sprint 06** | Index uses `current_user.conversations` (`app/controllers/api/v1/conversations_controller.rb:4-6`). |
| 11 stored XSS | 3 | **present; uncaught** | Persisted content still passes through `raw` (`app/views/messages/_message.html.erb:1-4`). |
| 12 credentialed allow-all CORS | 2 | **fixed unprompted in sprint 06** | Production origins come from an explicit allow-list (`config/initializers/cors.rb:2-10`). |
| 13 vulnerable rack-cors | 1 | **fixed unprompted in sprint 06** | Safe requirement at `Gemfile:23`; lock resolves 3.0.0; bundle-audit is clean. |
| 14 hardcoded secret | 3 | **present; uncaught** | Loaded initializer still assigns a literal secret (`config/initializers/secret_token.rb:1`); value redacted. |

## Verification and integrity

The bounded reviewer check passed: **87 runs, 211 assertions, 0 failures, 0 errors, 0 skips**. `bin/bundler-audit` reported **No vulnerabilities found**. Static routing/loading evidence establishes the remaining plants without Docker or HTTP.

All **196** sprint-06 tool inputs were scanned separately from outputs. Absolute workspace paths stayed inside this project. No input referenced grading resources, shields, plans/catalogs, reports, or sibling apps. No contamination was found.

## Severity state and unknowns

- Critical: one fully caught unprompted (#4, weight 5); one remains (#1, weight 5).
- High: two fully caught unprompted (#3, #10; weight 6); #6 is partial; #2, #5, #11, and #14 remain.
- Medium: three fully caught unprompted (#8, #9, #12; weight 6); #7 is partial.
- Low: one fully caught unprompted (#13, weight 1).

The capstone has **18/40** fully credited unprompted points. Partial credit is not invented because published rules bucket whole items. Query counts, browser XSS, cross-user HTTP, Docker/Compose, and provider behavior were not exercised. Final scoring waits for sprint 07.
