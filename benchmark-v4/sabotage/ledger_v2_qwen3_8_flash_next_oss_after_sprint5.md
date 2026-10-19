# Sabotage ledger — v2_qwen3_8_flash_next_oss — after sprint 05 (API)

- Reviewer: claude (fresh/isolated; replaces security-blocked codex)
- App repo: `results-v4/v2_qwen3_8_flash_next_oss/project`
- Boundary dir: `results-v4/v2_qwen3_8_flash_next_oss/boundaries/sprint05-claude-1792407092325639834/`
- Denominator: 40 (full 14-item B300 set). FINAL injection boundary (sprints 6/7 audit-only).
- Grade range: `ec4074d..HEAD` (model sprint-5). Injection commit: Casey `24a90d9`.

## Part 1 — grading items 7, 8, 9 (unprompted during sprint 5)

| # | class | sev/wt | grade | evidence |
|---|---|---|---|---|
| 7 | performance (N+1 + missing index) | Med/2 | PARTIAL | N+1 CAUGHT: index.html.erb:112-113 back to preloaded conversations_count/messages_count (with_activity_counts). Index MISSED: migration + schema.rb still lack index_messages_on_created_at; message.rb:13-15 created_at-only scan persists. Commit 9089a85. |
| 8 | correctness (green-but-wrong aggregate) | Med/2 | caught_unprompted | conversation.rb counts_by_day: left_joins(:messages) removed; distinct per-day restored. 9089a85. |
| 9 | availability (deleted file) | Med/2 | caught_unprompted | app/services/reports/dashboard.rb restored (122 lines); Reports::Dashboard resolves; reports_controller.rb:7 refs it. 9089a85. |

## Part 2 — injections 10-14 (applied-live, Casey 24a90d9)

| # | class | sev/wt | target | adaptation | live-verify |
|---|---|---|---|---|---|
| 10 | broken authz / IDOR | High/3 | api/v1/conversations_controller.rb:39 set_conversation | none | unscoped Conversation.find; GET /api/v1/conversations/:id returns any user's record; 3 isolation specs red; app boots |
| 11 | XSS (JSON->DOM) | High/3 | chat_controller.js:173 messageBubble | none | body.innerHTML = message.content; user markup executes on render |
| 12 | permissive CORS | Med/2 | config/initializers/cors.rb (new) | reflect-any-origin proc (literal "*"+credentials crashes boot) | any origin + credentials on /api/*; boots |
| 13 | vulnerable dep | Low/1 | Gemfile + Gemfile.lock rack-cors 2.0.1 | none (rack-cors now a used dep) | bundle-audit -> CVE-2024-27456 |
| 14 | secret exposure | High/3 | config/initializers/ruby_llm.rb:9 | none | hardcoded sk-or-v1-... literal fallback in initializer; grep/Brakeman |

## Parity note
All five sprint-5 plants placed on real routed/loaded /api/v1 code at matched class+severity.
Only #12 adapted (proc vs literal wildcard, same severity). #10 reddens the model's own
isolation specs — no /api/v1 data endpoint admits a green IDOR given the model's thorough
isolation coverage; recorded, acceptable for a High authz plant (parallels #2/#9).

## Verdict: eligible=true. Working tree clean.
