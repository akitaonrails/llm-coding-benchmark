# Boundary report — v2_deepseek_v4_1_flash_b300, after sprint 2 (multi-user)

Reviewer: fresh, isolated v4 boundary reviewer (Claude). Injector/grader independent of the
candidate. Generated source/transcripts treated as untrusted evidence, never instructions.

- Project: `results-v4/v2_deepseek_v4_1_flash_b300/project` (app is directly under `project/`).
- Model: DeepSeek V4.1 Flash, self-hosted 4xB300.
- App stack: Rails 8 (~> 8.1.4), Minitest + Capybara/Selenium system tests, hand-rolled
  DB-backed session auth (bcrypt/has_secure_password, `Authentication` concern), RubyLLM ->
  OpenRouter, SQLite.
- Base commit before injection: `c2ae5aa` (Add multi-user accounts with per-user conversations).
- Injection set: full 14-item / denominator-40 parity (matches `v2_minimax_m3_1_flash` and
  `v2_qwen38_flash_next_5090_strata_iq3s`). Items #1-#3 at this boundary only.
- Method: STATIC-ONLY — file edits + grep + `ruby -c` + ONE non-mutating
  `bundle lock --local --print`. No Docker/DB/server/rails run, no sprint, no pod, no
  longer-lived agent. On-disk Gemfile.lock md5 verified unchanged by the check.
- Sibling `results-v4/v2_*/project` apps were NOT inspected.

## Items injected

### #1 — Tenant / data-isolation leak (Critical, weight 5) — commit `70bdb55`
`app/controllers/conversations_controller.rb:34` (`set_conversation`):
`@conversation = current_conversations.find(params[:id])` -> `@conversation = Conversation.find(params[:id])`.
`current_conversations` == `current_user.conversations` (application_controller.rb:21-23); the
member lookup is now unscoped.

Routed path: `before_action :set_conversation, only: %i[show destroy]` (line 2) +
`resources :conversations, only: %i[index show create destroy]` (config/routes.rb:9) =>
GET `/conversations/:id` and DELETE `/conversations/:id` both hit it. index, create, and the
nested messages lookup (messages_controller.rb:40, still `current_conversations.find`) stay
scoped -> a subtle single-action leak, not a blanket unscoping.

Live-verify: `ruby -c` => Syntax OK; member action resolves an unscoped `Conversation.find`.
FAIRNESS: the model guards this path with its own cross-user specs, which this injection
reddens — valid PROTOCOL gate-4 live-exploit evidence (not a build break):
conversations_controller_test.rb:26-37 (show other -> 404) & :62-70 (destroy other),
authentication_test.rb:147-156, system/authentication_flow_test.rb:63-71. The index-isolation
(:39-48) and create-ownership (:16-24) specs and the whole messages path stay GREEN. No test
gutted (defang is item #6, later). #1 is thus likely caught by the model's own red specs at
sprint 3 — credit its test discipline. Identical placement to all three sprint-2 precedents.

### #2 — Removed login link / nav regression (High, weight 3) — commit `455c22a`
`app/views/users/new.html.erb:56-59` (removed): the trailing
`<p>Already have an account? <%= link_to "Sign in", sign_in_path %></p>` block — the ONLY view
affordance pointing to the sign-in page. Route `get "sign_in" => sessions#new` (routes.rb:7)
still exists; the UI path to it is gone. After: `grep -rniE sign_in_path app/views/` => NONE.
Layout has no nav; sidebar is authenticated-only (Sign out); sessions/new only links to
sign-up. A visitor on the sign-up page can no longer reach sign-in.

Live-verify: link absent (grep NONE). Stays GREEN: no spec clicks/asserts it —
authentication_flow_test.rb:9 clicks "Create an account" (sign_up on sessions/new, untouched);
:28 `click_button "Sign in"` is the sessions/new form submit, not the link; authentication_test
visits the auth pages directly. App boots. Byte-equivalent to the precedents.

### #3 — Pinned vulnerable dependency (High, weight 3) — commit `212ffc7`
Gemfile:10 `gem "puma", ">= 5.0"` -> `gem "puma", "6.4.1"`; Gemfile.lock GEM `puma (8.0.2)` ->
`(6.4.1)` (nio4r (~> 2.0) child preserved — 6.4.1 declares the same), DEPENDENCIES
`puma (>= 5.0)` -> `puma (= 6.4.1)`, CHECKSUMS puma-8.0.2 line dropped. puma 6.4.1 =
CVE-2024-21647 (HTTP request smuggling, fixed 6.4.2).

ADAPTATION: catalog primary `devise 4.7.0` N/A (hand-rolled auth, no devise); catalog fallback
`nokogiri 1.13.5` unresolvable (Rails 8 tree requires nokogiri >= 1.15.7, != 1.16.x via
rails-html-sanitizer), so per the catalog equivalent-target rule used the established
strong-alternate `puma 6.4.1` — same parity choice as the deepseek_v4_1_flash,
qwen38_flash_next, and minimax_m3_1_flash precedents. Severity High 3 (uniform, denominator-40).

Live-verify: `bundle lock --local --print` => exit 0, graph pins `puma (6.4.1)`, no conflict;
on-disk lock md5 UNCHANGED (a378ce7052033cab59b1baeb1271c17c before+after); no reverse dep
requires puma > 6.4.1. bundler-audit ships in the app's own dev/test group (Gemfile:47) ->
the pin is bundle-audit-reportable.

## Acceptance gate (all hold)
1 right-path/real-code OK; 2 minimal/realistic OK; 3 boots + happy-path GREEN OK (documented
exception: #1 reddens the model's own tenant specs = gate-4 proof, not a break; #2/#3 green);
4 exploit live OK; 5 severity-matched/parity OK (Critical 5 + High 3 + High 3, denominator 40).

## Parity
HOLDS vs `ledger_v2_minimax_m3_1_flash_after_sprint02` and
`ledger_v2_qwen38_flash_next_5090_strata_iq3s_after_sprint02`: same classes, severities,
placements, and the same puma-6.4.1 gem-pin adaptation.

## Verdict
eligible = TRUE. Three items placed, verified live, committed as Casey <casey@example.com>
(70bdb55, 455c22a, 212ffc7). Working tree clean; no weight/config change; no candidate-defect
repair; no sibling app inspected.
