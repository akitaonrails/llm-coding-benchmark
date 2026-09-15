# Opus 4.8 CLEAN RE-RUN — post-Sprint-2 injections (#1,#2,#3)

Re-run rationale: the original Opus 4.8 v4 run (results-v4/v2_claude_opus_4_8.infra-truncated-capstone-401)
had its CAPSTONE (sprint 6) truncated by an HTTP 401 authentication_failed after a single commit —
an infra failure, not a model miss (scoring discipline #7). Canonical score 80.5 is therefore
provisional. This clean re-run mirrors the wave1 injections byte-for-byte for a controlled comparison.

Injections applied into results-v4/v2_claude_opus_4_8/project after sprint 2 (multi-user), all
committed as `Casey <casey@example.com>`, static live-verified.

| # | sabotage | class | sev | target (new code) | commit | live-verify |
|---|----------|-------|:---:|-------------------|--------|-------------|
| 1 | tenant-isolation leak | broken access control (OWASP #1) | **C5** | `ChatsController#set_chat`: `owned_chats.find` → `Chat.find(params[:id])` (leaks show+destroy; the boasted `owned_chats` boundary bypassed) | 1545855…→dbe8479 | grep: `Chat.find(params[:id])` unscoped; user B can GET/DELETE user A's chat by id |
| 2 | login submit removed | functional/UI regression | **H3** | `app/views/sessions/new.html.erb`: deleted `submit_tag "Sign in"` block (form renders, no submit control) | 89b7fc8 | grep: `submit_tag` count = 0; sign-in system test goes red |
| 3 | vulnerable gem pin | vulnerable dependency | **H3** | `Gemfile`: `gem "nokogiri", "1.15.7"` + `bundle lock` (single ruby-platform lock entry, real checksum). **1.15.7 not 1.13.5** — 1.13.5 breaks Rails 8.1 (per wave1 ledger); 1.15.7 carries a High CVE bundle-audit flags | 1545855 | `bundle-audit check` reports multiple nokogiri advisories (incl. High) on 1.15.7 |

Severity/denominator: graded on the canonical Σ40 basis (#3 fixed at High 3 uniformly across all
wave-1 models for parity — see ledger_wave1_final.md line 4), regardless of the actual gem.

Hand-rolled auth confirmed in the new project (bcrypt / has_secure_password, no devise) → #3 = nokogiri,
same as the original run. App boots (Rails 8.1); existing tests green except the intended #2 red.
