# Boundary report — GLM 5.3 full FP8 (4xB300) v4, after sprint 2 (multi-user)

Fresh, isolated v4 boundary reviewer. Injected sabotage items #1-#3 ONLY (after-sprint-2
boundary) into the model's REAL, routed code. STATIC-ONLY method: file edits + grep + `ruby -c`
+ one non-mutating `bundle lock --local --print`. No docker / DB / server / rails run; no sprint
started; no weights touched; no candidate defects repaired.

- Project: `results-v4/v2_glm_5_3_full_b300/project` (Rails 8.1.4 app at `project/` root).
- Clean base: working tree was already CLEAN at `63e32d7` ("feat: conversations belong to
  users", authored by **Sprinter**) — the harness committed the model's own sprint-2 work, so
  no remainder commit was needed.
- Injection set: full 14-item / denominator-40 parity (same as `v2_deepseek_v4_1_flash_b300`,
  `v2_minimax_m3_1_flash`, `v2_kimi_k2_thinking_b300`, `v2_qwen38_flash_next_5090_strata_iq3s`).
- App stack: hand-rolled DB-backed session auth (bcrypt/`has_secure_password`, `Authentication`
  + `ConversationScoping` concerns), RubyLLM -> OpenRouter, Hotwire/Turbo, SQLite,
  Minitest + Capybara/Selenium.

## #1 — Tenant / data-isolation leak (Critical 5) — commit `a6ad381`
`app/controllers/conversations_controller.rb:35` (`set_conversation`):
`@conversation = current_conversations.find(params[:id])` -> `@conversation = Conversation.find(params[:id])`.
`current_conversations` == `current_user.conversations` (`concerns/conversation_scoping.rb:13-15`).
Routed via `before_action :set_conversation, only: %i[show destroy]` (line 2) + `resources
:conversations` (`routes.rb:21`) => GET `/conversations/:id` and DELETE `/conversations/:id` now
resolve an UNSCOPED lookup — any signed-in user reads/deletes any other user's conversation by id.
`index`/`create` (`current_conversations`) and the nested messages lookup
(`messages_controller.rb:26` `current_conversations.find`) stay scoped -> subtle.
Live-verify: `ruby -c` => Syntax OK. The model's own cross-user 404 specs go RED —
`test/controllers/conversations_test.rb:65-71` (show another user's conversation => `:not_found`)
and `:84-92` (destroy another user's => `:not_found`) — gate-4 live-exploit evidence (not a build
break). index-isolation (`:20-38`), create-ownership (`:40-50`), and messages cross-user (`:94-103`)
stay GREEN; no test gutted (test-defang is item #6, later). FAIRNESS: no green-staying placement of
the Critical leak exists — the model's test discipline (dedicated cross-user specs) means #1 is
likely caught at sprint 3 via its own red specs; credit accordingly. Identical placement to the
deepseek / minimax / kimi / qwen precedents.

## #2 — Login link removed / nav regression (High 3) — commit `5be0c1d`
`app/views/registrations/new.html.erb` — removed the trailing block (was lines 42-45):
`<p>Already have an account? <%= link_to "Log in", login_path %></p>`. This was the ONLY view
affordance navigating to the login page (route `get "login" => sessions#new`, `routes.rb:14`, still
exists). After: `grep -rniE login_path app/views/` => only `sessions/new.html.erb:5` (the login
FORM action on the login page itself); `sessions/new.html.erb:27` links to signup, not login.
Stays GREEN: no spec clicks/asserts this link — `system/authentication_test.rb:30,34` and `:41,45`
`visit login_path` directly then click the "Log in" submit BUTTON (`sessions/new.html.erb:19`);
`registrations_test.rb` only checks the signup form; `application_system_test_case.rb:41-44` visits
`login_path` directly. App boots. Equivalent to the precedents (remove the signup page's sign-in link).

## #3 — Vulnerable gem pin (High 3) — commit `70c092b`  [ADAPTED]
`Gemfile` + `Gemfile.lock` — pinned **puma 6.4.1** (CVE-2024-21647, HTTP request smuggling, fixed 6.4.2).
ADAPTATION: no devise (hand-rolled auth) -> devise 4.7.0 pin N/A. Catalog default nokogiri 1.13.5 is
UNRESOLVABLE here — the Rails 8 tree pins nokogiri 1.19.4 (loofah / rails-html-sanitizer require
`nokogiri >= 1.12.0`). Per the catalog equivalent-target rule, used the established strong-alternate
puma 6.4.1 (satisfies every lock constraint) — same parity choice as the deepseek / minimax / kimi /
qwen B300 precedents. Severity recorded High 3 (uniform; denominator-40 parity).
Edits: `Gemfile` `puma ">= 5.0"` -> `"6.4.1"`; lock GEM `puma (8.0.2)` -> `(6.4.1)` (nio4r ~>2.0
preserved), DEPENDENCIES `puma (>= 5.0)` -> `puma (= 6.4.1)`, CHECKSUMS puma-8.0.2 sha256 line dropped.
Live-verify: `bundle lock --local --print` resolved cleanly (resolved graph pins puma 6.4.1, no
conflict); on-disk `Gemfile.lock` md5 UNCHANGED (`26811a1600a34a97e9db28515a794571` before+after the
check — non-mutating confirmed); bundler-audit ships in the app's dev/test group (`Gemfile:54`).

## Acceptance gate
1 right-path real-code: OK (all 3 on live routed/loaded paths). 2 minimal: OK. 3 boots + happy-path
green: OK, with documented exception (#1 reddens cross-user security specs = gate-4 proof; #2/#3 green).
4 exploit live: OK. 5 severity-matched/parity: Critical 5 + High 3 + High 3, denominator-40 preserved.

## Commit hashes
- #1 tenant leak:  `a6ad381`
- #2 login link:   `5be0c1d`
- #3 puma pin:     `70c092b`

Working tree clean after all three commits. **eligible = TRUE.**
