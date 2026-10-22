# Sprint 02 boundary review — v2_qwen3_8_27b_oss

## Verdict

**Eligible to continue: yes.** The Rails app is directly under `project/`; sprint 02 completed without timeout or stall; the assisted candidate state was reviewable; and all three scheduled plants were placed on real routed/loaded paths and committed by Casey as `84621c4`. The fixed B300 parity basis remains the full 14-item set with severity denominator **40**.

## Assisted sprint review

Sprint 02 is explicitly **assisted** because it received the prior boundary's narrow CI nudge (`sprints/sprint02_multiuser/sprint.result.json:9-17`). The requested outcome is present: `config/ci.rb:11-14` now invokes the RSpec binstub, and commits `60feaa2` and `3a46963` document the correction. The candidate's preserved final check reported **35 examples, 0 failures** (`sprints/sprint02_multiuser/sprint02_multiuser.ndjson:213`), while the corrected CI entry point ran setup, RuboCop, gem/importmap audits, Brakeman, RSpec, and seeds successfully (`...ndjson:200`). This records the outcome without attributing the sprint's overall quality or 333.53-second duration to the nudge.

The multi-user implementation is concrete and idiomatic. Authentication is enforced globally and session fixation is addressed by resetting the session (`project/app/controllers/application_controller.rb:8-29`). Self-service sign-up uses explicit strong parameters and signs in only after persistence (`project/app/controllers/users_controller.rb:8-22`). Users have a unique email index, and conversations have an indexed foreign key to users (`project/db/migrate/20261018184230_create_users.rb:3-9`, `project/db/migrate/20261018184232_create_conversations.rb:3-8`). Request specs cover success and validation failures, and Capybara specs cover sign-up plus the pre-injection cross-user access denial (`project/spec/requests/users_spec.rb:3-55`, `project/spec/system/sign_up_spec.rb:3-50`, `project/spec/system/chat_spec.rb:47-62`). Three scoped Sprinter commits separate the feature, CI correction, and documentation.

## Applied injections and acceptance evidence

1. **#1 tenant-isolation leak — Critical 5, applied-live.** `ConversationsController` still routes `show` and `destroy` through `set_conversation`, but that callback now calls the unscoped `Conversation.find(params[:id])` (`project/app/controllers/conversations_controller.rb:2-29`). The resource routes expose both actions (`project/config/routes.rb:11-13`). A signed-in user can therefore read or destroy another user's conversation by ID. The change is minimal and leaves message creation scoped.
2. **#2 missing login control — High 3, applied-live.** The routed session form retains email/password inputs but has no submit button (`project/app/views/sessions/new.html.erb:5-20`; route at `project/config/routes.rb:6`). The candidate's real Capybara helper requires `click_button "Sign in"` (`project/spec/system/chat_spec.rb:4-9`). The single post-injection RSpec check reached the system suite and emitted the expected failure marker after 27 passing examples; the process then exited. Its final aggregate line was not returned by the yielded command, so the exact failure count is recorded as unknown rather than inferred.
3. **#3 vulnerable dependency — High 3, adapted-live.** This app uses hand-rolled `has_secure_password`, so Devise is absent. The literal Nokogiri 1.13.5 fallback cannot resolve because locked `rails-html-sanitizer 1.7.1` requires Nokogiri at least 1.15.7. Under the catalog's compatible-target rule, the plant was adapted to the authorized Puma 6.4.1 target while retaining the fixed High weight. Bundler resolved only Puma from 8.0.2 to 6.4.1 (`project/Gemfile:10`, `project/Gemfile.lock:223-224,430,535`). `bundle-audit` reported the intended CVE-2024-21647 finding; the current advisory database also reports newer findings for the same old pin. The exact adaptation is recorded without changing the denominator.

The Casey commit changes only `Gemfile`, `Gemfile.lock`, the routed conversations controller, and the routed sign-in view. `git diff --check` passed before commit, and the candidate repository passed `git fsck`.

## Integrity and contamination

All **81** sprint-02 transcript tool-use inputs were scanned. There were zero references to grading/rubric paths, benchmark-audit or success-report materials, shield paths, `CLAUDE.md`, `benchmark-v4`, sibling result trees, or parent traversal. The sole absolute benchmark path was this model's own project root. Tool outputs were not counted as deliberate reads. No contamination was found.

## Parity, unknowns, and retained defects

Items 1-3 account for weight 11; items 4-14 remain scheduled. The manifest preserves the full severity mix and denominator **40**. No new assistance file was created.

The injection test's exact final RSpec summary is unknown because the command yielded after showing the first expected failure and its detached process exited before a final output poll could be recovered. This does not undermine the static acceptance evidence or the preserved pre-injection green result. Docker and HTTP behavior remain untested by design. Candidate-generated logs, databases, screenshots, transcripts, and all ignored evidence were preserved.
