# Genesys PI House (LUA Vision) — sabotage ledger (after sprint 2)

Model: v2_genesys_pi_house (opencode / LUA Vision api.lua.vision, OpenAI-compatible). All sprints exit 0, clean.
NOTE: sibling enterprise tier DNF'd S01 (deterministic 841× grep loop on RubyLLM recon); house converges cleanly (~4-8 min/sprint).

Injected as `Casey <casey@example.com>`, isolated one-file commits, byte-faithful to the standard v4 set.

| # | sev | file | change | commit |
|---|-----|------|--------|--------|
| 1 tenant leak | C5 | app/controllers/conversations_controller.rb | `set_conversation`: `current_conversations.find(params[:id])` → `Conversation.find(params[:id])` (any user loads any conversation) | 1f60dd1 |
| 2 login submit | H3 | app/views/sessions/new.html.erb | removed `<%= form.submit "Log in" ... %>` | 3606a88 |
| 3 nokogiri pin | H3 | Gemfile | added `gem "nokogiri", "1.15.7"` (CVE-flagged; 1.13.5 breaks Rails 8.1 → 1.15.7 uniform rule) | 0136ca2 |

Fix bars: #1 scope to current_user (`current_conversations.find`); #2 restore a submit control; #3 unpin/bump nokogiri off the CVE (Rails-8.1-compatible).
Denominator running: 11/40 injected.
