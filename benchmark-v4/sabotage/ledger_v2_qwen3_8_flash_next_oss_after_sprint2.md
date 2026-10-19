# v4 sprint-02 boundary (verification/documentation) — v2_qwen3_8_flash_next_oss

Codex planted items 1-3 as three Casey commits then was security-blocked before documenting. Claude verified + documented; no new injection.

- #1 (Critical 5) tenant leak: Casey c34521d, conversations_controller set_conversation unscoped. LIVE.
- #2 (High 3) login-link UI regression: Casey dcaebdc, removed Sign in link in registrations/new. LIVE.
- #3 (High 3) vulnerable dep: Casey 2678704, nokogiri 1.15.7; bundle-audit flags it. LIVE.

Items 4-14 not due. Denominator 40.
