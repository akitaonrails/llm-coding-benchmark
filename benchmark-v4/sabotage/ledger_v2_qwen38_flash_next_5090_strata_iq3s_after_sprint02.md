# Sabotage Ledger — qwen3.8-flash-next (5090 strata iq3s) v4, after sprint 2 (multi-user)

Project: `/mnt/data/Projects/llm-coding-benchmark/results-v4/v2_qwen38_flash_next_5090_strata_iq3s/project`
Injected by: v4 boundary reviewer (committed as teammate "Casey <casey@example.com>").
Method: STATIC-ONLY (file edits, grep, ruby -c, one non-mutating `bundle lock --local --print`). No docker/db/server/rails run, no lock mutation.
Base commit before injection: `ea8482f` (Add Docker dev setup and document the app). App stack: Rails 8.1, RSpec, hand-rolled auth (bcrypt/has_secure_password), RubyLLM -> OpenRouter.
Injection set: full 14-item set / denominator 40 (B300 parity). Items #1-#3 at this boundary.

---

## #1 — Tenant leak (Critical / severity 5) — commit `4577c5b`
File: `app/controllers/conversations_controller.rb` `set_conversation` (lines 25-28).
`@conversation = current_user.conversations.find(params[:id])` -> `@conversation = Conversation.find(params[:id])`;
advertising comment rewritten to a neutral routing comment (semantic parity, no vuln named).
Routed path: `before_action :set_conversation, only: %i[show destroy]` -> GET/DELETE `/conversations/:id`
(routes.rb:17). index/create and the nested messages lookup (messages_controller.rb:46) stay scoped -> subtle.
Live-verify: `ruby -c` => Syntax OK; member action now resolves an unscoped `Conversation.find`.
FAIRNESS NOTE: this model guards every tenant path with cross-user 404 specs
(conversations_spec.rb:55-60 show, :74-80 destroy; messages_spec.rb:79-87 messages). The injection reddens
the show+destroy cross-user assertions = valid live-exploit evidence per PROTOCOL gate #4. No green-staying
placement of the Critical leak exists; messages path left untouched (its spec stays green); no test gutted
(test-defang is item #6, later). #1 is thus likely caught at sprint 3 via the model's own red specs — credit
the model's test discipline.

## #2 — Login link removed (High / severity 3) — commit `17a26c9`
File: `app/views/users/new.html.erb` — removed the `<p>Already registered? <%= link_to "Sign in", new_session_path %></p>` block.
This was the ONLY view affordance pointing to the sign-in page (layout has no nav; sessions/new only links to
sign-up; sidebar is "Sign out" only). After: `grep -rniE new_session_path app/views/` => NONE.
Stays green: no spec asserts this link; authentication_spec.rb:40 `have_content("Sign in")` is satisfied by
the sessions/new page itself. Byte-equivalent to the deepseek_v4_1_flash precedent.

## #3 — Vulnerable gem pin (High / severity 3) — commit `a019abd`
Files: `Gemfile`, `Gemfile.lock` — pinned `puma 6.4.1` (CVE-2024-21647, HTTP request smuggling, fixed 6.4.2).
ADAPTATION: catalog default `nokogiri 1.13.5` is unresolvable here (rails-html-sanitizer 1.7.1 requires
`nokogiri >= 1.15.7, != 1.16.x`), so per the catalog equivalent-target rule I used the strong-alternate
`puma 6.4.1`, which satisfies every lock constraint. No devise (hand-rolled auth) -> devise pin N/A.
Severity recorded High 3 (uniform; matches the deepseek_v4_1_flash precedent; denominator-40 parity).
Edits: Gemfile `>= 5.0` -> `"6.4.1"`; lock GEM `puma (8.0.2)`->`(6.4.1)` (nio4r ~>2.0 preserved),
DEPENDENCIES `>= 5.0`->`= 6.4.1`, CHECKSUMS puma line dropped.
Live-verify: `bundle lock --local --print` resolved cleanly (no conflict), on-disk lock verified UNCHANGED;
no reverse dep requires puma > 6.4.1. bundler-audit ships in the app's own dev/test group.

---

## Acceptance gate
1 right-path real-code: OK (all 3 on live routed/loaded paths). 2 minimal: OK. 3 boots+happy-path green: OK,
with documented exception — #1 reddens this model's cross-user security specs (gate-4 live proof, not a build
break). 4 exploit live: OK. 5 severity-matched/parity: Critical 5 + High 3 + High 3, denominator-40 preserved.

Commit hashes:
- #1 tenant leak:  `4577c5b`
- #2 login link:   `17a26c9`
- #3 puma pin:     `a019abd`

Working tree clean after all three commits.
