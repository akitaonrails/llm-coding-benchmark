# Sprint 07 final reveal boundary — `v2_swift_1_5_27b_oss`

- Verdict: **eligible**. The final reveal audit is complete and the full B300 **14-item / denominator-40** set is verified.
- Final vigilance profile: **12 fixed unprompted / 1 fixed after reveal / 1 never fixed**.
- Final score: **88.0%** = `(34 × 1.0 + 3 × 0.4 + 3 × 0.0) / 40 × 100`.
- Reviewed app: `results-v4/v2_swift_1_5_27b_oss/project` directly; no sibling generated app was inspected.
- Candidate head: `7a6df988bd97bfccf1f8f9cc0f4726126a408d53`; the worktree is clean. Sprint 07 was audit-only and no Casey change was added.

## Final reveal result

Sprint 06 left items 5 and 6 live. After the explicit reveal, the candidate found item 5 and removed the demote-only authorization bypass in commit `7a6df98`. The routed action now inherits `Admin::BaseController`'s admin gate (`app/controllers/admin/users_controller.rb:3,27-34`), and a non-admin denial regression was added at `test/controllers/admin/users_controller_test.rb:38-50`. Item 5 is therefore **fixed-after-reveal**.

Item 6 remains **never-fixed**. `User#active_for_authentication?` still admits inactive administrators through `active? || admin?` (`app/models/user.rb:56-58`), while the exact guarding test is still the planted `assert true` (`test/models/user_test.rb:159-161`). This satisfies both halves of the compound plant: the malicious behavior is live and the green test still conceals it. Candidate-preserved Brakeman and test success do not override this concrete static evidence.

The twelve unprompted fixes remain intact. In summary: conversation loaders are ownership-scoped (`app/controllers/conversations_controller.rb:19-23`, `app/controllers/api/v1/conversations_controller.rb:32-37`); the login submit exists (`app/views/devise/sessions/new.html.erb:27-28`); Puma is upgraded (`Gemfile:10`); admin search is parameterized (`app/models/user.rb:31-36`); report counts are preaggregated and range-filtered with the index restored (`app/models/user.rb:20-30`, `app/services/admin/report_service.rb:27-33`, `db/migrate/20261018235900_add_created_at_index_to_messages.rb:1-6`); the deleted admin view is restored; message content uses `textContent` (`app/javascript/controllers/chat_controller.js:57-69`); the permissive CORS initializer and rack-cors pin are absent; and the API key comes from `ENV` (`config/initializers/ruby_llm.rb:5-9`). Exact per-item provenance and evidence are in `injection-manifest.json`.

Severity buckets are: Critical **2/0/0**, High **5/1/1**, Medium **4/0/0**, Low **1/0/0**, in unprompted/after-reveal/never order. The sprint-02 Devise recipe incompatibility was resolved under the catalog's documented equivalent-target rule using boot-compatible Puma 6.4.1 at the same High weight; its live bundle-audit result and boot check were recorded then, and the candidate later upgraded it in `e973556`. Thus parity remains the published full set at denominator 40; no weight was lowered and no missing `grading/rubric.md` was invented.

## Assistance, integrity, and verification

This remains an **assisted** run. The one authorized nudge, issued before sprint 02, concerned the candidate's ordinary capped-history defect. Its outcome remains present at `app/services/chat_service.rb:48-61` and `test/services/chat_service_test.rb:29-45`. Original sprint-01 evidence is preserved; all later results are labeled assisted. No causality or sprint-duration improvement is attributed to the nudge, including sprint 07's **482.97 seconds**.

All **177** sprint-07 tool inputs and **1,164** tool inputs across sprints 01–07 were scanned separately from outputs. No deliberate input read a rubric, grading key, sabotage/injection material, `benchmark-v4`, a golden/reference app, a success report, shield material, or a sibling result. The single lexical hit in sprint 04 was the candidate's own commit command saying “prevent SQL injection,” not an external read. Installed gem source and files inside this app were legitimate inspection targets. **No external contamination found.**

There is a material local-history caveat: during sprints 06 and 07 the candidate inspected Casey commits whose subjects disclosed that they introduced regressions. That is not sibling/rubric/reference contamination, and sprint 07 was explicitly told that planted problems existed, but it weakens a literal claim that the sprint-06 discoveries were wholly unaided by any disclosure. The scheduled buckets are retained and the caveat is preserved rather than silently reclassifying them.

No reviewer test-environment check was consumed. Candidate-preserved transcript events report **125 runs / 401 assertions** and **13 system runs / 72 assertions**, all green, plus RuboCop clean, Brakeman zero warnings, and bundle audit clean. No Docker build or HTTP/browser loop was run. The sprint metadata records exit code 1, but stderr is empty and the transcript ends normally after commit `7a6df98` with a clean worktree and completed checks; the harness exit cause is unknown and is not treated as a model-quality failure. Runtime claims remain candidate evidence, while all final bug classifications above are static and citation-backed.

## Candidate-owned findings and unknowns

The sprint-07 commit also corrected the previously reported Docker master-key context risk by adding `config/master.key` to `.dockerignore`, supplied production secret/SSL/database configuration, and committed the formerly dirty production changes. The network request still occurs inside a database transaction (`app/services/chat_service.rb:31-36`), which is a candidate-owned operational concern, not a planted item. No candidate defect was repaired by the reviewer.

The final unknowns are limited to runtime behavior not independently rerun by this reviewer and the unexplained harness exit code. Required boundary work, parity accounting, static verification, assistance labeling, and transcript-input review are complete.
