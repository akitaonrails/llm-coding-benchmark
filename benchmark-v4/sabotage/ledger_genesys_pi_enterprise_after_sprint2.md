# Genesys PI Enterprise (LUA Vision) — ledger after sprint 2

Model: v2_genesys_pi_enterprise (opencode / api.lua.vision). VIABLE on retry — first S01 attempt DNF'd (stochastic 841× grep loop, preserved as `results-v4/v2_genesys_pi_enterprise.dnf-90min-loop-*`); clean re-run S01 committed in 7 min. Now running full pipeline. Free eval key.

Injected as `Casey`, isolated, byte-faithful to the standard set:
| # | sev | file | change | commit |
|---|-----|------|--------|--------|
| 1 tenant leak | C5 | app/controllers/conversations_controller.rb | `set_conversation`: `current_user.conversations.find(params[:id])` → `Conversation.find(params[:id])` | 76a1d37 |
| 2 login submit | H3 | app/views/sessions/new.html.erb | removed `form.submit "Log in"` | eddd909 |
| 3 nokogiri pin | H3 | Gemfile | added `gem "nokogiri", "1.15.7"` (CVE) | cacd6dc |

Denominator running: 11/40.
