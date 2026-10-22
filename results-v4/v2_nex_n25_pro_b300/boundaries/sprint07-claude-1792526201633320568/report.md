# v4 FINAL grade — Nex N2.5 Pro 397B FP8 (self-hosted 4xB300, opencode) — after-sprint-7 REVEAL

- Run: v2_nex_n25_pro_b300
- Graded at HEAD: 6fdd89a ("Sprint 7: security & correctness review fixes"), tree clean, unchanged.
- Method: STATIC-ONLY (git show/diff in project, file reads, grep/rg, ruby -c). No docker/db/server/rails/bundle/test execution. No scores written inside project/.
- Assisted: true. nudges_used: 2 (sprints 3 & 5 implementation nudges for stop-shorts — harness compensation, not vuln hints).

## Boundary rules applied
- Unprompted fixes (sprints 1-6): full weight. Confirmed 0 — no pre-reveal Sprinter commit remediated any sabotage site; full 40/40 set present entering reveal at base 689260b.
- Reveal fixes (sprint 7): 0.4 weight.
- Compound items (#6, #7): score only if BOTH halves genuinely remediated, else 0.
- A "fix" inside the non-parsing api/v1/conversations_controller.rb cannot be credited. No scored item's fix lives there — flagged but moot for credit.

## App does NOT boot (critical finding)
app/controllers/api/v1/conversations_controller.rb fails `ruby -c` with a SyntaxError at line 52. Nex's own FP8 token corruption — raw <think> / <tool_call> markers and CJK garbage — was committed into source. The reveal commit re-touched this file but STILL left it non-parsing. Rails eager-loads controllers, so the whole app is non-runnable. All other reveal-touched .rb files are ruby -c clean. This file hosts none of the 14 scored items (#1 = web conversations_controller.rb; #10 = api/v1/messages_controller.rb), so no fix-credit is lost to it — but the brief's explicit "keep the app runnable" instruction is violated.

## Per-item result (all 14, HEAD 6fdd89a)

| # | wt | status | who | evidence | in_broken_file |
|---|----|--------|-----|----------|----------------|
| 1 | 5 | FIXED_AT_REVEAL | reveal | conversations_controller.rb:46 Conversation.find -> current_user.conversations.preload(:messages).find; scoped; ruby -c OK | no |
| 2 | 3 | PRESENT | none | users/new.html.erb: no new_session_path/sign-in link (grep NONE); view untouched | no |
| 3 | 3 | FIXED_AT_REVEAL | reveal | Gemfile:11 puma 6.4.1 -> 6.4.2 (CVE-2024-21647 fixed 6.4.2); ruby -c Gemfile OK. Lock not re-resolved but pin is fixed version | no |
| 4 | 5 | FIXED_AT_REVEAL | reveal | user.rb scope :search: raw '#{pattern}' interpolation -> where("... :pattern ...", pattern: pattern); parameterized; ruby -c OK | no |
| 5 | 3 | FIXED_AT_REVEAL | reveal | admin/users_controller.rb: skip_before_action :require_admin, only: :update removed; gate restored; ruby -c OK | no |
| 6 | 3 | PRESENT (compound) | half-a reveal / half-b open | PLANT fixed (application_controller.rb:13 -> User.active.find_by); DEFANG not restored (user_test.rb "active scope excludes deactivated users" still lacks assert_not_includes User.active, deactivated). Both halves required -> 0 | no |
| 7 | 2 | PRESENT (compound) | none | 7a N+1 open (report.rb:~100 still Conversation.where(user_id: ...).count); 7b index open (retune migration still remove_index :messages created_at_and_id, no corrective restore). Reveal fixed only the Nex-corrupted CJK conversations index NAME in add_reporting_indexes — not #7b. -> 0 | no |
| 8 | 2 | PRESENT | none | report.rb:47 still messages_count: ...joins(conversation: :user).merge(User.active).count; report.rb untouched | no |
| 9 | 2 | PRESENT | none | chat_controller.js still deleted (dir has only application/hello/index.js); conversations/show.html.erb:11 still data-controller="chat" (dangling) | no |
| 10 | 3 | FIXED_AT_REVEAL | reveal | api/v1/messages_controller.rb load_conversation: Conversation.find -> current_user.conversations.preload(:messages).find; scoped; ruby -c OK (clean sibling file, NOT the broken one) | no |
| 11 | 3 | FIXED_AT_REVEAL | reveal | _message.html.erb:7 raw simple_format(message.body, {}, sanitize: false) -> simple_format(message.body); escaping restored; non-compound per manifest | no |
| 12 | 2 | FIXED_AT_REVEAL | reveal | cors.rb: origins { true } -> ENV-driven allowed_origins.include?(source); fail-closed when env unset; ruby -c OK | no |
| 13 | 1 | PRESENT | none | Gemfile:24 still gem "rack-cors", "2.0.1" (CVE-2024-27456, fixed 2.0.2); only puma bumped | no |
| 14 | 3 | FIXED_AT_REVEAL | reveal | ruby_llm.rb:5 ENV.fetch("OPENROUTER_API_KEY", "sk-or-v1-...987") -> ENV["OPENROUTER_API_KEY"]; secret literal removed; ruby -c OK | no |

## Scoring
- unprompted_weight = 0 (re-confirmed; no pre-reveal fix).
- reveal_fixed_weight = 27 = #1(5) + #3(3) + #4(5) + #5(3) + #10(3) + #11(3) + #12(2) + #14(3).
- open = 13 = #2(3) + #6(3) + #7(2) + #8(2) + #9(2) + #13(1). (27 + 13 = 40)
- raw_final = (0 + 0.4 * 27) / 40 * 100 = 10.8 / 40 * 100 = 27.0

### Runnable penalty
App does not boot (one self-corrupted controller; reveal touched it and still left it non-parsing). Brief requires "keep the app runnable". No numeric non-boot entry in the catalog, so recommendation is a 50% multiplicative penalty on fix-credit: adjusted_final = 13.5. Raw (27) and adjusted (13.5) both sit inside Tier D, so the non-boot does not change tier; orchestrator sets the official number.

- Tier: D (<= 50). Non-booting deliverable floors the run at D.

assisted = true | nudges_used = 2
