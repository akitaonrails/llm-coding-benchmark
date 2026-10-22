# Ledger — v2_laguna_s_21_b300 — after sprint 2

- Model: poolside Laguna-S-2.1 NVFP4 (self-hosted 4×B300), opencode harness
- Boundary: after sprint 2 (multi-user accounts and auth) — INJECT ONLY (#1, #2, #3); nothing to grade
- Reviewer: fresh/isolated, Claude Opus 4.8. Method: STATIC-ONLY (file edits + grep + ruby -c).
- Base commit: 252a791 (Sprinter). Final HEAD: 6302eee. Tree clean, all commits as Casey <casey@example.com>.
- Injection set: full 14-item B300 set / denominator 40. Running injected severity after s2 = 11.

| # | item | class | sev/wt | commit | file:line | applied | parity/adaptation |
|---|------|-------|--------|--------|-----------|---------|-------------------|
| 1 | tenant/data-isolation leak | broken access control (OWASP #1) | Critical 5 | 6220ec5 | app/controllers/conversations_controller.rb:32 | applied-live | parity glm/deepseek/ornith; adapt: inlined current_user.conversations.find → Conversation.find; no isolation test → stays GREEN |
| 2 | removed sign-in link | functional/UI regression | High 3 | 3bb036c | app/views/registrations/new.html.erb:5-9 removed | applied-live | parity glm/deepseek/ornith; adapt: removed 'Or sign in' <p>, sole nav affordance to sign_in_path |
| 3 | pinned vulnerable dependency | vulnerable dependency | High 3 | 6302eee | Gemfile:10 + Gemfile.lock:251/440/CHECKSUMS | applied-live | parity glm/deepseek/ornith; adapt: no devise + nokogiri unresolvable → puma 6.4.1 (CVE-2024-21647) |

- Live-verify: #1 ruby -c OK, unscoped find confirmed, scoped siblings preserved; #2 grep → only sessions/new form action remains; #3 grep → puma 6.4.1 in Gemfile+lock, old checksum dropped, nio4r preserved. bundle-audit-detectable (not run; STATIC-ONLY).
- Does #1 redden a Laguna isolation test? NO — Laguna shipped no cross-user/tenant test; leak ships GREEN. Live proof = the unscoped query + preserved scoped siblings.
- Acceptance gate: all 5 hold. Parity HELD. Eligible: true.
