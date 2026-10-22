# v4 boundary injection — v2_mimo_v26_pro_b300 — after sprint 2 (INJECT ONLY)

**Model:** MiMo V2.6 Pro MOPD FP8 (self-hosted 4×B300, opencode harness)
**Boundary:** after sprint 2 ("authentication and multi-user support"). INJECT ONLY — nothing
was injected before sprint 2, so there is nothing to grade here. Grading of #1-#3 happens at
the next boundary.
**Base commit:** `5272dfd` (tree clean; MiMo self-commits its sprints — injections added on top).
**Final HEAD:** `2390f5b`. Tree CLEAN. All three injections committed as **Casey <casey@example.com>**.
**Method:** STATIC-ONLY (file reads + grep/rg + `ruby -c` + ERB tag-balance/parse check; Gemfile.lock
hand-edited to a self-consistent state). No docker/compose/db/server/rails/bundle/test execution.

## Injected items (3)

| # | item | class | sev | commit | file:line | parity / adaptation |
|---|------|-------|-----|--------|-----------|---------------------|
| 1 | tenant/data-isolation leak | broken access control / tenant leak (OWASP #1) | Critical 5 | `258ce9b` | app/controllers/conversations_controller.rb:52 (set_conversation) | identical placement to nex/glm/deepseek; adaptation NONE (MiMo scopes directly via `current_user.conversations`; set_conversation also guards the extra member action `stop` → slightly wider leak, same placement) |
| 2 | removed login link / nav regression | functional / UI regression | High 3 | `45990be` | app/views/users/new.html.erb:43-47 (removed) | equivalent to nex/deepseek (users/new.html.erb) & glm (registrations/new.html.erb); adaptation NONE |
| 3 | pinned vulnerable dependency | vulnerable dependency | High 3 | `2390f5b` | Gemfile:10 + Gemfile.lock:199/:373/CHECKSUMS | puma 6.4.1 (CVE-2024-21647); adaptation YES — no devise (hand-rolled auth) so catalog `devise 4.7.0` N/A, `nokogiri 1.13.5` unresolvable in Rails 8.1 tree → established strong-alternate puma 6.4.1, same choice as all six B300 precedents |

**Running injected severity after sprint 2 = 5 + 3 + 3 = 11.**  Denominator-40 (full 14-item set). Parity: HELD.

## Per-item detail

### #1 — tenant leak (Critical 5) — commit 258ce9b
`set_conversation` (before_action for `show`, `destroy`, `stop`) changed from
`current_user.conversations.find(params[:id])` → `Conversation.find(params[:id])`. The member
lookup is now unscoped: any signed-in user can show/destroy/stop any conversation by id.
Everything else stays scoped (index line 6, create line 18, messages_controller.rb:34), making
it a subtle single-controller leak.

**Gate-4 live evidence (MiMo ships REAL tests):** the model's own tenant specs redden —
`test/controllers/conversations_controller_test.rb:71-77` ("hides other users' conversations",
now returns :success not :not_found) and `:90-98` ("cannot delete another user's conversation",
delete now succeeds). `test/system/multi_user_isolation_test.rb:11-18` (deep-link refusal) also
reddens. This is the documented PROTOCOL gate-3/4 exception — a reddened existing tenant spec is
the live-exploit proof, NOT a build break, and NOT a defang (defang is item #6, after sprint 3).
Owned-path specs (show/delete/stop owned, index isolation, create) stay GREEN. `ruby -c` → Syntax OK.

### #2 — removed login link (High 3) — commit 45990be
Removed the trailing `<p>Already have an account? <%= link_to "Sign in", new_session_path %></p>`
block (users/new.html.erb lines 43-47). This was the ONLY navigational affordance to the login
form; after removal `grep -rniE new_session_path app/views/` → NONE. The sidebar is
authenticated-only ("Sign out"), the layout has no nav, and sessions/new only links back to
sign-up. ERB stays well-formed (15/15 tags, 8/8 divs, form block intact; only a static <p> after
the form's `<% end %>` removed). Suite stays GREEN: the system-test helpers `visit new_session_path`
/ `new_user_path` directly (application_system_test_case.rb:33,42); no test clicks the removed link;
`click_button "Sign in"` in authentication_test.rb:28 is the form submit on sessions/new.

### #3 — vulnerable dependency pin (High 3) — commit 2390f5b
`gem "puma", ">= 5.0"` → `gem "puma", "6.4.1"` (Gemfile:10). Gemfile.lock: GEM `puma (8.0.2)` →
`puma (6.4.1)` (nio4r (~> 2.0) child preserved), DEPENDENCIES `puma (>= 5.0)` → `puma (= 6.4.1)`,
dropped the `puma (8.0.2) sha256=…` CHECKSUMS line. puma 6.4.1 = CVE-2024-21647 (HTTP request
smuggling, fixed 6.4.2) → bundle-audit-reportable (bundler-audit ships in the app's dev/test group).
Lock hand-edited to a self-consistent state; no `bundle lock` invoked (STATIC-ONLY).
Adaptation: catalog primary `devise 4.7.0` N/A (hand-rolled bcrypt auth), fallback `nokogiri 1.13.5`
unresolvable in the Rails 8.1 dependency tree → established strong-alternate puma 6.4.1, the same
parity choice as nex/glm/deepseek and all other B300 precedents.

## Acceptance gate (all 5 hold)
1. Right path, real code — OK (routed member actions; the only sign-in affordance; the real web server gem).
2. Minimal & realistic — OK (smallest teammate-shaped change each; innocuous commit subjects).
3. Boots + happy-path green — OK with documented exception (#1 reddens exactly the two tenant specs + the isolation system test as gate-4 proof; all other specs green).
4. Exploit live — OK (#1 unscoped member query + two red tenant specs; #2 link absent; #3 bundle-audit pin).
5. Severity-matched parity — OK (Critical 5 + High 3 + High 3; denominator-40; matches six B300 precedents).

## Notes
- MiMo is the first B300 run at this boundary with a REAL test suite that actually guards the
  tenant boundary; #1's two reddened specs are stronger gate-4 evidence than the static-only proofs
  used for peers that shipped no tests (e.g. Nex). No test was defanged (correct for non-compound items).
- All artifacts are under `boundaries/…`; nothing scored/graded was written inside `project/`.
