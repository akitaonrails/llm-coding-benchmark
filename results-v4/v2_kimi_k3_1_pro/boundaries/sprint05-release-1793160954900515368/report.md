# v4 boundary report: v2_kimi_k3_1_pro, after sprint 05 (grade-only mode)

**Verdict: INELIGIBLE (awaiting_injection: 10, 11, 12, 13, 14).** This boundary grades #7-9 and requires #10-14 to be planted. None of #10-14 have been planted, and none qualifies as N/A.

The review was static only: code inspection, git, and transcript parsing. I ran no test, no Docker, and no HTTP. I made no edits, commits, stages, stashes or resets in the candidate project, and `git status` is clean.

## Inputs inspected
- Protocol docs: CLAUDE.md, benchmark-v4/{PROTOCOL, FULL_RUN_PROCEDURE, INJECTION_PLAN, SABOTAGE_CATALOG, README}.md, sabotage/after_sprint4.md and after_sprint5.md (recipes), and wave ledgers for #7 partial precedent.
- Earlier boundaries for this model: sprint01, sprint02, sprint03 (×2), and sprint04 (×3), each with verdict, injections and report.
- Previous sprint-05 attempts: **none**. This directory is the first sprint-05 boundary, and its `agent.ndjson` is this review's own transcript.
- `boundaries/human_injections.json`: `{"7": 5bce200, "8": "N/A: ...", "9": 27de99f}`. It has no keys 10-14.
- Sprint-05 candidate run: `sprints/sprint05_api/` (exit 0, 6,465,891 tokens, $1.84, 1405 s, not stall-aborted). The discarded first attempt (`_failed_sprints/sprint05_api.failed-auth-1793157373`) was an auth crash with 0 tokens. It was not charged to the model, per PAUSED...resolved-globbug.

## Git log (Casey commits = all planted items)
| commit | author | item |
|---|---|---|
| 49c5a8d / e9a97f6 / 807a7e9 | Casey | #1 / #2 / #3 (sprint 02, llm-reviewer) |
| f890442 / 5f1bccb / 01e1dc2 | Casey | #4 / #5 / #6 (sprint 03, llm-reviewer) |
| 5bce200 / 27de99f | Casey | #7 / #9 (sprint 04, human; #8 N/A) |
| 5106077, 0fefcdb | Sprinter | sprint-05 candidate work (HEAD) |

**There is no Casey commit after 0fefcdb, so none of #10-14 has been planted.**

## Injection acceptance checks (#10-14)
| # | class / severity | status | evidence that a target exists (so not N/A) |
|---|---|---|---|
| 10 | API broken authz, High 3 | **MISSING** | `app/controllers/api/v1/conversations_controller.rb:5,29`, `messages_controller.rb:21` (current_user-scoped) |
| 11 | XSS, High 3 | **MISSING** | `app/javascript/controllers/chat_controller.js:135` renders message content (currently `textContent`) |
| 12 | permissive CORS, Med 2 | **MISSING** | `/api/v1` namespace at `config/routes.rb:7-8`; the recipe allows adding a CORS config |
| 13 | rack-cors 2.0.1 pin, Low 1 | **MISSING** | rack-cors is absent; the recipe says "else add it" |
| 14 | hardcoded secret, High 3 | **MISSING** | `config/initializers/` (e.g. `ruby_llm.rb`) |

No acceptance test could run, because there is no commit to test. The operator has to plant all five as Casey commits and list them in `human_injections.json`. After that, a re-run boundary will apply the per-class acceptance checks: recipe class/severity, minimal edit, live path, equivalent target, neutral message, and the class-appropriate test-greenness rule.

## Grading: items due at this boundary (#7-9)
| # | sev | provenance | status | evidence |
|---|---|---|---|---|
| 7 | Med 2 | human (5bce200) | **PARTIAL: N+1 fixed, index still dropped** | N+1 half fixed unprompted in 5106077: `app/models/reporting/dashboard.rb:20-33` uses one grouped `Conversation.left_joins(:messages).group(:user_id)` aggregate instead of per-user `.count`. The candidate retightened its own guard from 8 to 7 queries (`test/models/reporting/dashboard_test.rb:56`). Index half NOT fixed: `db/migrate/20261027230000_drop_messages_created_at_index.rb` remains, and `db/schema.rb` messages table has only the `[conversation_id, created_at, id]` composite (line 30), with no `index_messages_on_created_at`. That composite cannot serve the `daily_counts(Message, created_at range)` scan at `dashboard.rb:40,52-54`. The transcript noticed only the "14 queries instead of 8" symptom. Under the wave's strict compound rule (Grok 4.6 / Kimi K3 / DeepSeek ledgers: #7b index missed means #7 is not credited), the item currently earns **0**. It can still be fully fixed at 06/07. |
| 8 | Med 2 | N/A (operator) | **EXCLUDED** | Operator N/A: all aggregates are exact-pinned by `test/models/reporting/dashboard_test.rb`. The denominator is reduced 40 → 38 and the run is flagged as a **reduced item set** (carried from sprint04 boundary 1793155665069877204). |
| 9 | Med 2 | human (27de99f) | **FIXED unprompted** | Transcript call #46: `git show HEAD^:app/views/conversations/_sidebar.html.erb`. The candidate recovered the deleted partial's content from git history and folded it into the new API-driven `app/views/conversations/_chat.html.erb:6-27` (same brand link, New chat, conversation nav, email, admin links and Log out). `index.html.erb`/`show.html.erb` now render `conversations/chat`, so there is no dangling `render "conversations/sidebar"` (grep finds none). The candidate's final suite in the transcript shows 90 runs, 0 failures, 0 errors, so the app is whole. Minor note: this was a git-informed re-integration, not a literal `git restore`. That is acceptable because the sprint refactored the same view into the API-driven layout, and precedent credits git-informed re-creation. |

### Earlier items: current state (informational; formal unprompted grading is at sprint 06)
| # | sev | provenance | state at 0fefcdb | evidence |
|---|---|---|---|---|
| 1 | Crit 5 | llm-reviewer | fixed (s03) | `conversations_controller.rb:23` `current_user.conversations.find`; API also scoped |
| 2 | High 3 | llm-reviewer | **still present** | `app/views/registrations/new.html.erb` has no `link_to` back to log in |
| 3 | High 3 | llm-reviewer | fixed (s03) | Gemfile.lock:200 `puma (7.2.1)`; transcript shows bundler-audit "No vulnerabilities found" |
| 4 | Crit 5 | llm-reviewer | fixed (s04) | `app/models/user.rb:23` bound `?` with `sanitize_sql_like` |
| 5 | High 3 | llm-reviewer | fixed (s04) | `admin/users_controller.rb` has no `skip_before_action :require_admin` |
| 6 | High 3 | llm-reviewer | **fixed unprompted in sprint 05 (both halves)** | 5106077: `application_controller.rb:15` restores `User.active.find_by`, and the gutted test `test/integration/admin_users_test.rb:99-108` is rebuilt with real assertions (redirect plus API 401). This changes the sprint-04 "PRESENT" state. |

**Provisional weights (denominator 38):** unprompted = #1 5 + #3 3 + #4 5 + #5 3 + #6 3 + #9 2 = **21**. Reveal = 0 and never = 0, because those are assigned only at sprint 07. #7 has 0 so far. #2 is still open. #10-14 (12 points) are not yet planted, so the denominator assumes they will be: 40 − 2 (#8 N/A) = 38.

## Ordinary minor defects (not repaired)
- The dropped `messages.created_at` index (#7b) leaves the 30-day activity query unindexed on `messages`.
- The sign-up page lacks a log-in link (#2).
- Commit hygiene: sprint 05 bundles API, JS rewrite, report fix, the #6 repair and the sidebar recovery into one large commit (5106077, 35 files) plus a README commit. The commits are well described but not atomic.

## Contamination scan (sprint-05 candidate transcript, 165 tool calls)
- **Tool inputs:** 0 hits for CLAUDE.md, rubric, audit_prompt, bench_shield, v4shield, success_report, benchmark-audit, benchmark-v4, sabotage, human_injections, boundaries, or any sibling `results-v4/v2_*`. There were 0 repo paths outside `v2_kimi_k3_1_pro/project`.
- **Out-of-workspace tool calls (incidental, judged clean):**
  - one `mcp__ai-memory__memory_recent {"limit":10}` call returned 10 unrelated global memory titles (game ports, distrobox, lint report) with 0 matches for sabotage/Casey/inject/boundary/rubric/benchmark/score/sidebar;
  - one `Skill verification-planning` call came from the user-global skills;
  - one Write of a plan file into kimi's own session dir (`~/.kimi-code/sessions/...`).

  The ai-memory MCP is an isolation gap to note for the operator, because the cross-project memory is reachable from candidate runs. It leaked nothing here.
- **Incidental output hits:** "CLAUDE.md" appears twice, only in ai-memory hook boilerplate text, not as a read. No sibling slug appears anywhere.
- **Verdict:** clean.

## Denominator
38 (Tier-A full 14-item set, 40, minus #8 N/A at 2). **This is a REDUCED ITEM SET run**, and it must be noted for within-tier parity. #10-14 (12 points) are still required and outstanding.
