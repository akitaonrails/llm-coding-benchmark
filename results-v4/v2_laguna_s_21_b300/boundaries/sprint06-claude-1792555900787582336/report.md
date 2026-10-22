# Boundary review — after sprint 6 capstone (GRADE-ONLY)

- **Run:** `v2_laguna_s_21_b300` — poolside Laguna-S-2.1 NVFP4 (self-hosted 4×B300, opencode harness)
- **Boundary:** after_sprint6_capstone (vague "harden for production", full unprompted weight)
- **HEAD:** `295ceb7` ("Security: fix IDOR in API messages controller"), tree clean, self-committed by Laguna (author Sprinter)
- **Mode:** static-only (file reads, grep, git, ruby -c, node --check). No injection. No commits.

## Capstone commit scope
`295ceb7` is one self-authored commit. Its message claims an API IDOR fix + secret removal + filter params + tests, but the diff reaches further and closes **6** planted defects (some unmentioned in the message).

## 14-item final unprompted status at HEAD

| # | Item | Wt | Status | Fix commit | Evidence | Both halves |
|---|------|----|--------|-----------|----------|-------------|
| 1 | web IDOR conversations_controller#show | 5 (Crit) | PRESENT | — | conversations_controller.rb:33 `Conversation.find(params[:id])` unscoped; capstone untouched | n/a |
| 2 | removed sign-in link | 3 (High) | PRESENT | — | layouts/application.html.erb nav only inside `if current_user`; no anon sign-in link | n/a |
| 3 | puma 6.4.1 (CVE) | 3 (High) | FIXED | 295ceb7 | Gemfile `~> 8.0`, lock 8.0.2 | n/a |
| 4 | admin-search SQLi | 5 (Crit) | FIXED | b6ac758 (s5, incidental) | admin/users_controller.rb `where("email ILIKE ?", "%#{@q}%")` bound param; no regression | n/a |
| 5 | admin skip_before_action :require_admin only: :deactivate | 3 (High) | PRESENT | — | admin/users_controller.rb:7 still present; capstone only trimmed a trailing space | n/a |
| 6 | COMPOUND current_user active + defanged user_test | 3 (High) | PRESENT | — | Half1 active-guard fixed s4 (authentication.rb); Half2 user_test defang PERSISTS (72dbe4d dropped `assert_not user.active?`, still gone) | Half1 fixed, Half2 PRESENT → 0 |
| 7 | COMPOUND N+1 + dropped index + gutted test | 2 (Med) | PRESENT | — | N+1 loop in dashboard.rb per_user_breakdown; index_conversations_on_created_at dropped (migration 20261021130000); N+1 test gutted to smoke-check (ee8e16b) | all 3 halves PRESENT → 0 |
| 8 | wrong aggregate User.all.count (active_users) | 2 (Med) | FIXED | 295ceb7 | dashboard.rb count_active_users `User.active.count` (`-User.all.count`) | n/a |
| 9 | deleted-but-wired chat_form_controller.js | 2 (Med) | PRESENT | — | file deleted (ce0c1da); still wired in conversations/show.html.erb + messages/_form.html.erb (`chat-form#request`) | n/a |
| 10 | API IDOR api/v1/messages_controller | 3 (High) | FIXED | 295ceb7 | set_conversation `current_user.conversations.find(...)` (`-Conversation.find`) | n/a |
| 11 | XSS raw user body _message.html.erb | 3 (High) | PRESENT | — | user branch `<%= raw message.content %>`; capstone untouched | n/a |
| 12 | CORS any-origin + credentials | 2 (Med) | FIXED | 295ceb7 | cors.rb: reflect-any + credentials:true replaced by env origins (default `*`) with credentials off when wildcard | n/a |
| 13 | rack-cors 2.0.1 | 1 (Low) | FIXED | 295ceb7 | Gemfile `~> 3.0`, lock 3.0.0 (`-2.0.1`) | n/a |
| 14 | hardcoded OpenRouter secret ruby_llm.rb | 3 (High) | FIXED | 295ceb7 | `ENV["OPENROUTER_API_KEY"]`; capstone removed the `sk-or-v1-...987` literal fallback (re-added pre-capstone in 58096be) | n/a |

## Capstone newly-fixed (6 items, weight 14)
#3 puma, #8 User.all.count, #10 API IDOR, #12 CORS, #13 rack-cors, #14 hardcoded secret.

**Notable asymmetry:** the capstone fixed the API IDOR (#10) but left the identical class in the web `conversations_controller#show` (#1, Crit 5) — a partial, class-incomplete remediation. It also did not touch #5 (admin auth skip), #11 (XSS raw), #9 (deleted-wired JS), the #6 test defang, or the #7 compound.

## Tally
- **Cumulative unprompted caught: 19 / 40** (FIXED: #3,#4,#8,#10,#12,#13,#14 = 3+5+2+3+2+1+3).
- Entering capstone caught = 5 (only #4). Capstone added +14 → 19.
- **Open entering reveal: 7 items, weight 21** — #1 (5), #2 (3), #5 (3), #6 (3), #7 (2), #9 (2), #11 (3). 19 + 21 = 40 ✓.

## app_boots (static)
`ruby -c` on every app/config .rb → all Syntax OK. `node --check` on every app/javascript .js → all OK. **app_boots = true** (syntax sound). Caveat: #9 leaves the chat form wired to a missing Stimulus controller — a runtime functional break, not a boot/syntax failure.

## Integrity
Tree untouched, HEAD remains `295ceb7`, no scores/identities written inside `project/` (all artifacts under `boundaries/`). All checks static.
