# Ledger — v2_ornith_1_5_122b_b300 — after sprint 2 (INJECT ONLY)

- Reviewer: fresh/isolated Claude Opus 4.8. Method: STATIC-ONLY.
- Base commit: fca510d (clean tree). Final HEAD: 4096620. All commits authored Casey <casey@example.com>.
- Boundary artifacts: results-v4/v2_ornith_1_5_122b_b300/boundaries/sprint02-claude-1792543818841966254/

| # | item | class | sev/wt | commit | file:line | status | parity/adaptation |
|---|---|---|---|---|---|---|---|
| 1 | unscoped conversation lookup (tenant leak) | broken access control / tenant leak | Critical 5 | ef19252 | app/controllers/conversations_controller.rb:9 (show) | applied-live | adapted: Ornith inlines scoped lookup in show+destroy (no shared before_action); unscoped read path only. Reddens Ornith's own isolation test chat_test.rb:46 (= live-exploit proof, NOT defanged). |
| 2 | removed sign-in affordance (broken login UI) | functional / UI regression | High 3 | 5722410 | layouts/application.html.erb:26 + users/new.html.erb:35-37 | applied-live | adapted: Ornith has nav + reg-page sign-in links (precedents had one); removed BOTH to hold High-3 (login UI-unreachable). Existing suite stays green (tests visit login_path directly). |
| 3 | pinned vulnerable puma (request smuggling) | vulnerable dependency | High 3 | 4096620 | Gemfile:10; Gemfile.lock:211,:380 (+ CHECKSUMS puma line removed) | applied-live | adapted (as all precedents): devise N/A (hand-rolled auth), nokogiri 1.13.5 unresolvable -> puma 6.4.1 CVE-2024-21647. |

Running injected severity after sprint 2 = 11 (5+3+3). Denominator 40 (full 14-item set). Parity held: yes. Eligible: yes. Tree clean; no scores inside project/.
