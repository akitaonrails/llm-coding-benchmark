# v4 boundary review — sprint 02

- Model: `v2_ornith_1_5_35b_oss`
- Boundary: after `sprint02_multiuser`
- Verdict: **eligible to continue**
- Required injection: items **1–3**, all applied and verified
- Batch parity: full 14-item B300 set, severity denominator **40**
- Assistance: no prior assistance existed; sprint 02 is unassisted; no new assistance was issued

## Sprint and repository evidence

The sprint ledger records 423.86 seconds, 4,386,142 tokens, exit code 0, and no stall abort. It produced three descriptive Sprinter commits (`2b53ecd`, `c00ea01`, `92b0d42`) after the foundation. The worktree was clean and had no Casey commit when this review began, so no interrupted injection was duplicated.

The candidate retained the hand-rolled multi-user implementation and materially improved it: successful login and registration now call a shared `sign_in` helper that resets the session before assigning the user (`app/controllers/application_controller.rb:27-30`, `app/controllers/sessions_controller.rb:8-17`, `app/controllers/registrations_controller.rb:8-16`). User ownership remains expressed through associations (`app/models/user.rb:1-9`, `app/models/conversation.rb:1-3`), and the pre-injection conversation/message paths were scoped through `current_user.conversations` (`app/controllers/conversations_controller.rb` at parent commit `92b0d42`, lines 4-24; `app/controllers/messages_controller.rb:4-11`; `app/controllers/events_controller.rb:4-5`). The new system spec exercises signup, logout, login, bad credentials, and unauthenticated redirection (`spec/system/authentication_spec.rb:8-58`).

## Candidate-authored defects and unknowns

Before injection, request coverage still omitted cross-user show and destroy cases: it tests a user's own show/delete only (`spec/requests/conversations_spec.rb:22-54`), while only message creation has an explicit cross-user rejection assertion (`spec/requests/messages_spec.rb:32-41`). This is a real coverage gap but not grounds to stop or assist an otherwise reviewable sprint. The prior boundary's SSE framing and upstream-error disclosure observations also remain unresolved (`app/controllers/events_controller.rb:13-28`). No candidate defect was repaired.

One permitted RSpec check was attempted after the first dependency adaptation. It stopped before examples because catalog alternate MiniMagick 4.9.3 requires `benchmark`, which is no longer a Ruby 4 default gem. That adaptation was rejected and fully removed rather than patching the candidate or accepting broken boot. The final dependency set passes `bundle check` and a `Bundler.require(:default)` load; the suite was not rerun because this boundary allows at most one quick test-environment check. Full post-injection Rails-suite behavior is therefore unknown beyond the static evidence below. The intentional login-control regression is expected to conflict with `spec/system/authentication_spec.rb:27-37`.

## Injection ledger and verification

Casey commit `21099bd37bb1aeb76e99b8530b7fc7b5ff6149c6` (`Casey <casey@example.com>`, `Refine conversation lookup and API dependencies`) contains only the four prescribed dependency/controller/view files.

1. **Item 1 — Critical 5, applied-live.** The real `resources :conversations` route includes `show` (`config/routes.rb:7`). Its authenticated action now loads `Conversation.find(params[:id])` without owner scope (`app/controllers/conversations_controller.rb:2,8-9`), and the routed view renders that object's messages (`app/views/conversations/show.html.erb:1`, `app/views/conversations/_chat.html.erb:1-15`). Thus any logged-in user who supplies another user's ID reaches that conversation.
2. **Item 2 — High 3, applied-live.** The routed sessions resource includes `new` and `create` (`config/routes.rb:4`). The actual login page retains its credential form but has no submit control (`app/views/sessions/new.html.erb:1-22`), while the candidate's system spec still calls `click_button "Log in"` (`spec/system/authentication_spec.rb:27-37`). No inert or alternate view was edited.
3. **Item 3 — High 3, adapted.** This app uses `has_secure_password`, not Devise (`app/models/user.rb:1-2`). The literal Nokogiri 1.13.5 fallback is incompatible because locked `rails-html-sanitizer` requires Nokogiri >=1.15.7 (`Gemfile.lock:239-241`). The catalog-authorized High-severity equivalent `jwt 2.10.2` was therefore pinned (`Gemfile:11-12`, `Gemfile.lock:150,391`). `bundle-audit check --no-update` reports exactly `CVE-2026-45363`, Criticality High; `bundle check` and default-group loading succeed. This preserves item weight 3 and the denominator 40.

Items 4–14 remain `not-yet-injected`. The exact statuses and evidence are recorded in `injection-manifest.json`.

## Integrity and contamination

All 118 sprint-02 tool inputs were scanned for grading/rubric files, benchmark-audit material, success reports, audit prompts, shield paths, v4 protocol/injection/catalog files, and sibling `results-v4/v2_*` projects. There were zero sensitive or sibling-project matches. One read input used a broad `../../../*/actionpack-8.1.4/.../cookie_store.rb` glob while seeking gem source; it failed with no output and did not read a sibling app or grading resource. Incidental outputs were not treated as deliberate reads. No Docker, HTTP loop, pod, campaign setting, or sibling generated application was accessed.

## Boundary conclusion

The sprint review, commit audit, transcript-input contamination scan, full denominator-40 manifest, three required live-path injections, catalog-compatible dependency adaptation, Casey commit, and cleanup accounting are complete. Static evidence establishes the intended routed effects and bundle-audit finding; the one-check limit leaves the final full suite unrerun, which is recorded rather than guessed.
