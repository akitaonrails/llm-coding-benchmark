# Post-Sprint-2 injections (items 1,2,3) — apply into each model's REAL code, verify live

## Item 1 — Tenant-isolation leak (Critical 5, model/controller, opening: none)
RECIPE (fixed for both models): locate the controller action that fetches a user's
conversations for display (index and/or show), which after multi-user must be scoped to the
current user. Replace the scoped lookup with an UNSCOPED one — minimal edit:
  - `current_user.conversations`            -> `Conversation.all`
  - `current_user.conversations.find(id)`   -> `Conversation.find(id)`
  - `@conversations = current_user...`      -> `@conversations = Conversation.all`
Primary target: ConversationsController#index and #show (or equivalent). Acceptable
equivalents: any action/query that lists or loads a conversation for the logged-in user.
Make ONLY this change (subtle: single-user happy path still works).
LIVE-VERIFY: user A creates a conversation; logged in as user B, B's index shows it OR
B can GET /conversations/:id of A's — leak confirmed. App still boots; existing tests green.

## Item 2 — Login button/link removed (High 3, view, opening: none)
RECIPE: in the layout/nav/header partial that renders the "Log in" link/button (or on the
landing page), delete that link/button element only. Primary target: app/views/layouts/
application.html.erb nav, or the partial with `link_to ... login/session`. 
LIVE-VERIFY: the rendered nav/landing no longer contains a login control (grep the view;
render the page). If the model wrote a system test that logs in via that control, it goes
red — that's the intended catch. App still boots.

## Item 3 — Vulnerable gem pin (High/Med, Gemfile, opening: none)
RECIPE: if the model used devise -> pin `gem "devise", "4.7.0"` (CVE-2019-16109, High 3).
Else (hand-rolled auth) -> add `gem "nokogiri", "1.13.5"` (CVE-2022-29181, Med 2).
Then run `bundle install` (or `bundle lock`) so Gemfile.lock reflects the pin.
LIVE-VERIFY: `bundle-audit check --update` reports the exact CVE for that gem/version.
RECORD which gem was pinned (severity depends on it) in the parity ledger.

## Parity note
All three should apply to BOTH Tier-A models (both build multi-user + a login control +
Gemfile). Record applied/adapted/N-A per model. If any has no target in one model, adapt
to an equivalent target; if truly impossible, drop from BOTH.
