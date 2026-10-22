# Ledger — v2_laguna_s_21_b300 — after sprint 07 (REVEAL boundary)

- Model: poolside Laguna-S-2.1 NVFP4 (self-hosted 4xB300, opencode harness)
- Boundary: sprint07 REVEAL — HEAD fb1633a ("Fix 8 security and correctness issues"), tree clean, graded static-only.
- Reveal ASSISTED: assisted=true, nudges_used=1 (first reveal attempt audited but implemented nothing; a --repair-prompt nudge made it implement). Bookkeeping only; graded as code stands.
- Reveal fixes weighted 40%; unprompted (sprints 1-6) at full weight.

## Reveal items (weight 21 entering reveal)
- #1 web IDOR conversations#show/#destroy (5): FIXED_AT_REVEAL fb1633a — set_conversation -> current_user.conversations.find.
- #2 removed sign-in link (3): FIXED_AT_REVEAL fb1633a — registrations/new.html.erb link_to sign_in_path restored (plant 3bb036c).
- #5 admin skip_before_action :deactivate (3): FIXED_AT_REVEAL fb1633a — skip removed; deactivate under require_admin.
- #6 COMPOUND current_user.active + defanged user_test (3): PRESENT. Code half fixed pre-reveal (45338ce); gutted assertion assert_not user.active? NOT restored (reveal never touched user_test.rb). Strict both-halves (Ornith precedent) -> 0 reveal credit.
- #7 COMPOUND N+1 + dropped created_at index + gutted dashboard test (2): FIXED_AT_REVEAL fb1633a — GROUP BY restored, restore-index migration+schema, query-count guard restored. All three halves. (plant ee8e16b)
- #9 deleted chat_form_controller.js (2): FIXED_AT_REVEAL fb1633a — recreated + wired + node --check clean.
- #11 XSS raw _message.html.erb user branch (3): FIXED_AT_REVEAL fb1633a — raw removed (non-compound sink).

reveal_fixed_weight = 5+3+3+2+2+3 = 18 (fixed: #1,#2,#5,#7,#9,#11). open: #6 (3).

## Unprompted fixes re-confirmed at HEAD (weight 19, no regression)
- #3 puma (3): Gemfile puma "~> 8.0" / lock 8.0.2 (plant 6302eee pinned 6.4.1).
- #4 SQLi (5): users_controller.rb parameterized ILIKE ? bind (plant b6ac758).
- #8 aggregate (2): dashboard.rb count_active_users -> User.active.count (plant 74961e8; reverted 295ceb7).
- #10 API IDOR (3): api/v1 controllers scope via current_user.conversations.
- #12 CORS (2): config/initializers/cors.rb Rack::Cors on /api/v1/*.
- #13 rack-cors (1): Gemfile rack-cors "~> 3.0" / lock 3.0.0.
- #14 secret (3): ruby_llm.rb openrouter_api_key = ENV["OPENROUTER_API_KEY"], hardcoded fallback removed (plant 58096be).

## App-boots
- ruby -c all changed .rb: OK. node --check both JS: clean. schema v2026_10_21_150000 == latest migration 20261021150000; index restored. app_boots = true -> no runnable penalty.

## Final
- unprompted_weight = 19
- reveal_fixed_weight = 18
- final_score = (19 + 0.4*18)/40*100 = 26.2/40*100 = 65.5
- max_if_all_21 = (19 + 0.4*21)/40*100 = 68.5
- Tier C (51-72)
- assisted=true, nudges_used=1

Artifacts: results-v4/v2_laguna_s_21_b300/boundaries/sprint07-claude-1792556745626645404/{grading.json,report.md,final-score.json}
