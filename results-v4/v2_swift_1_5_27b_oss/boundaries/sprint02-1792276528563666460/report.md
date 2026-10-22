# Sprint 02 boundary review — `v2_swift_1_5_27b_oss`

- Verdict: **ineligible to continue** because the required item 3 injection cannot pass the fixed acceptance gate on this app; the boundary is intentionally partial rather than silently changing the recipe or denominator.
- Reviewed app: `results-v4/v2_swift_1_5_27b_oss/project` (Rails app directly at the project root; no sibling generated app was inspected).
- Candidate head before injection: `58f18f6366a26887703a7342e4d838423e62a356`.
- Partial Casey injection commit: `b8e4b3cb74622a790b5c9ba761dec8460f4259b4` (`Casey <casey@example.com>`).
- Campaign baseline: B300 full 14-item set, fixed severity denominator **40**. Items 1–3 are due here (weight 11); only items 1–2 (weight 8) are accepted.

## Assisted sprint outcome and static review

Sprint 02 is assisted. The sole prior nudge asked the candidate to verify capped LLM history. The candidate responded with the focused commit `58f18f6`, changing `app/services/chat_service.rb:48-61` to select the newest 50 messages before restoring chronological order, and strengthening `test/services/chat_service_test.rb:29-46` to assert that the current user turn survives. This directly addresses the ordinary defect identified at sprint 01. The run took 80.14 seconds within the existing cumulative budget; no causal timing attribution is made.

The multi-user feature remains substantive and routed: Devise owns authentication routes (`config/routes.rb:1-3`), application requests authenticate (`app/controllers/application_controller.rb:6`), conversations belong to users (`app/models/conversation.rb:2`), and candidate tests explicitly cover index/show/destroy isolation (`test/controllers/conversations_controller_test.rb:10-17,39-64`). No candidate source defect was repaired by the reviewer. The previously recorded production master-key/Docker-context risk and long transaction around provider work remain candidate-owned findings.

## Sprint-02 injection results

1. **Item 1 — tenant leak, Critical 5: accepted (`applied-live`, statically verified).** Casey changed the routed show/destroy loader to `Conversation.find(params[:id])` at `app/controllers/conversations_controller.rb:30-31`. `resources :conversations` routes show/destroy at `config/routes.rb:9-13`, while authentication still runs at `app/controllers/application_controller.rb:6`. Therefore any authenticated user who knows another user's id reaches that conversation instead of the prior `current_user.conversations.find`. The candidate's own isolation expectations at `test/controllers/conversations_controller_test.rb:39-45,57-64` concretely demonstrate the violated boundary. The change is one line and leaves same-owner behavior intact.
2. **Item 2 — login control removal, High 3: accepted (`applied-live`, statically verified).** Casey removed only the submit control from the live Devise session form. `devise_for :users` exposes the session route (`config/routes.rb:3`); `app/views/devise/sessions/new.html.erb:6-28` still renders the email/password form but has no submit button. The candidate's system flow requires `click_button "Sign in"` at `test/system/chat_flow_test.rb:33-41`, so that user-facing login flow is now broken exactly as prescribed.
3. **Item 3 — Devise 4.7.0 pin, High 3: rejected and reverted (`not-applied`).** The exact prescribed pin resolved and `bundle-audit check --no-update` reported CVE-2019-16109 for Devise 4.7.0 (plus two later Devise advisories). However, the single permitted quick test-environment check could not boot Rails: Devise 4.7.0 calls removed `ActiveSupport::Dependencies.reference` from `devise.rb:325`, raising `NoMethodError` during `Bundler.require` from `config/application.rb:19`. This violates the acceptance requirement that the planted dependency remain subtle and the app still boot. The Gemfile and lockfile were restored to the candidate's Devise 5.0.4 state before the Casey commit. No compatibility monkeypatch, alternative gem, or severity substitution was invented.

Because item 3 is absent, required injection parity and the fixed denominator-40 set are not established. Items 1–2 are preserved in the Casey commit so a later authorized resolution can see exactly what landed and will not duplicate them. No v4 vigilance score is assigned at this incomplete boundary.

## Transcript contamination review

All 35 candidate sprint-02 `tool_use` inputs were scanned separately from tool outputs. No input referenced grading, rubric, sabotage, injections, `benchmark-v4`, a golden/reference app, shielding, success reports, or a sibling result. Absolute reads outside this project were limited to installed Active Record source used to validate the candidate's history query. **No contamination found.** Generated source and transcripts were treated only as untrusted evidence.

## Unknowns and boundary decision

Items 4–14 are not due and their feature-dependent targets remain unverified. Items 1–2 have concrete routed/loaded-path static evidence; no Docker, browser, HTTP, or rack-test loop was used. Runtime behavior beyond the one failed item-3 gate was not retested because the procedure permits only one quick test-environment check. The stale missing `grading/rubric.md` path was not treated as a blocker; the actual v4 catalog, recipe, and published scoring rules were used. Eligibility is false solely because required item 3 did not pass the acceptance gate, leaving the exact boundary and parity set incomplete.
