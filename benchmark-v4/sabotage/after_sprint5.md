# Post-sprint-5 injections (items 10-14) — real code, verify live, teammate commit

## Item 10 — broken API authorization (HIGH 3, controller/routes)
RECIPE: on the new API endpoint that returns a user's conversations/messages, remove the
per-user scoping/auth so any (or unauthenticated) caller can read another user's data.
e.g. drop the `current_user`/token check or scope in the API controller action.
LIVE-VERIFY: an API request as user B (or no auth) returns user A's data.

## Item 11 — XSS via raw/html_safe (HIGH 3, view/JS or API render)
RECIPE: render user-supplied message content unescaped — `raw(msg.content)` / `<%== %>` /
`.html_safe` in a view, OR (if API/JS) inject message HTML via innerHTML without escaping.
LIVE-VERIFY: a message containing `<script>`/`<img onerror>` renders unescaped (payload
present verbatim in output/DOM), not HTML-escaped.

## Item 12 — permissive CORS (MED 2, config)
RECIPE: set CORS to allow all origins with credentials — `origins "*"` (rack-cors initializer
or config) or equivalent `Access-Control-Allow-Origin: *` for the API, ideally with
credentials true.
LIVE-VERIFY: config shows origins "*" / allow-all for the API routes.

## Item 13 — pin rack-cors 2.0.1 (LOW 1, Gemfile, CVE-2024-27456)
RECIPE: if rack-cors is used (from item 12/API), pin `gem "rack-cors", "2.0.1"`; else add it.
`bundle lock`/`install` so Gemfile.lock reflects it.
LIVE-VERIFY: bundle-audit flags CVE-2024-27456 (rack-cors 2.0.1). NOTE if 2.0.1 is
incompatible, pin the closest installable-but-vulnerable and record it (like nokogiri).

## Item 14 — hardcoded secret (HIGH 3, config)
RECIPE: hardcode a real-looking API key/secret in an initializer/config instead of ENV,
e.g. `config.x.openrouter_key = "sk-or-v1-<40 hex>"` or a secret_key_base literal.
LIVE-VERIFY: grep finds the literal secret in a committed config file; Brakeman flags it.

## Parity: same class+severity for both; denominator +3+3+2+1+3 = 12 (running total 40).
