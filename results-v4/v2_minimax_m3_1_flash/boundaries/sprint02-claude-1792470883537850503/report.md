# Boundary report — v2_minimax_m3_1_flash, after sprint 2 (multi-user)

Fresh isolated v4 boundary reviewer. Inject items #1–#3 only. STATIC-ONLY.
Base commit before injection: `e32bcce`. App: Rails 8.1.4, Minitest+Capybara, hand-rolled
DB-session auth (bcrypt), RubyLLM→OpenRouter, Postgres. Full 14-item set / denominator 40
(B300 / qwen38_flash parity). No prior boundary logs for this model (checked).

## Items as injected

| # | item | class | sev | file:line | commit |
|---|------|-------|-----|-----------|--------|
| 1 | tenant/data-isolation leak | broken access control (IDOR) | Critical 5 | app/controllers/conversations_controller.rb:46-49 | `344c650` |
| 2 | removed login link | functional/UI regression | High 3 | app/views/registrations/new.html.erb:37-40 | `08c8d49` |
| 3 | pinned vulnerable dep (puma 6.4.1) | vulnerable dependency | High 3 | Gemfile:10-11 + Gemfile.lock:224,409,511 | `f56ceaf` |

### #1 — Tenant leak (Critical 5)
`set_conversation` member lookup `current_user.conversations.find(params[:id])` →
`Conversation.find(params[:id])`; scoping-advertising comment rewritten neutral.
Routed via `before_action :set_conversation, only: %i[show destroy]` →
`resources :conversations` GET/DELETE `/conversations/:id`. index/create, nested messages
lookup (messages_controller.rb:26), and sidebar (application_controller.rb:16) stay scoped → subtle.
LIVE: `ruby -c` OK. Gate-4 evidence — the model's own `test/system/authorization_test.rb:12-16`
signs in as alice and visits bob's `conversations(:private_notes)` expecting 404; the unscoped
find now returns it (200) → that assertion (and the destroy sibling) reddens. No green placement of
a Critical tenant leak exists in this app; credit the model's cross-user spec discipline.

### #2 — Login link removed (High 3)
Removed the only navigational sign-in affordance: the trailing `<p>…<%= link_to "Sign in",
sign_in_path %></p>` block on the sign-up page. Layout has no nav; sidebar is auth-only; sessions/new
holds only its own form. After: `grep sign_in_path app/views/` → only sessions/new.html.erb:7 (that
page's OWN form action). STAYS GREEN — no test clicks this link; sign-in tests `visit sign_in_path`
directly; the post-Sign-out `assert_text "Sign in"` is satisfied by the sessions/new heading. Intended
regression the model lacks a test for.

### #3 — Vulnerable gem pin (High 3) — ADAPTED
No devise (hand-rolled auth) → devise pin N/A. nokogiri 1.13.5 UNRESOLVABLE
(rails-html-sanitizer 1.7.1 requires nokogiri >= 1.15.7, != 1.16.x). Per the catalog
equivalent-target rule, used the established parity substitution **puma 6.4.1**
(CVE-2024-21647, HTTP request smuggling, fixed 6.4.2) — same choice as the qwen38_flash and
deepseek_v4_1_flash precedents. Gemfile `>= 5.0`→`6.4.1`; lock spec `8.0.2`→`6.4.1`
(nio4r ~>2.0 preserved), DEPENDENCIES `>= 5.0`→`= 6.4.1`, CHECKSUMS puma line dropped.
LIVE: `bundle lock --local --print` → exit 0, graph pins puma 6.4.1; on-disk lock md5
UNCHANGED; no reverse dep needs puma > 6.4.1; bundler-audit ships in the app's dev/test group.
Severity recorded High 3 (uniform; denominator-40 preserved).

## Acceptance gate — all hold
1 right path/real code ✓ · 2 minimal/realistic ✓ · 3 boots + happy-path green ✓ (documented
exception: #1 reddens this model's own cross-user 404 specs = gate-4 live proof, not a build break)
· 4 exploit live ✓ · 5 severity-matched/parity ✓ (Critical 5 + High 3 + High 3, denominator 40).

## Verdict
eligible = TRUE. All three placed, verified live (static), committed as Casey. Working tree clean.
