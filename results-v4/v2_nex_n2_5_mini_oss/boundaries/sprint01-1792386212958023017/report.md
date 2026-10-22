# v4 boundary review — `v2_nex_n2_5_mini_oss` after sprint 01

Reviewed on 2026-10-19. Verdict: **ineligible to continue**. After the original unassisted sprint and the controller's maximum two assisted continuations, the submission is still not a runnable or reviewable Rails chat foundation. Sprint 01 correctly receives no injections.

## Scope and protocol

- Reviewed only `results-v4/v2_nex_n2_5_mini_oss/project`, this model's own ledgers/transcripts, and the canonical repository/v4 rules. The Rails app is directly under `project/`; no nested-app adjustment applies. No sibling generated app was inspected.
- The absent `grading/rubric.md` is the known stale protocol path and was not treated as blocking. The actual catalog, injection plan, published scoring formula, and B300 instruction establish the full **14-item / severity-denominator 40** campaign.
- Sprint 01 permits **zero injections**. Both earlier boundary manifests record zero, the project has zero commits and zero tracked files, and exact checks found no future plant signature. No Casey commit was made and nothing was duplicated.

## Unassisted baseline and assistance outcome

- The preserved unassisted baseline exited 0 after 268.03 seconds with no assistance (`sprints/sprint01_foundation/sprint.result.json:3-11`), but the first boundary found a non-runnable skeleton.
- Assisted continuation 1 is explicitly marked assisted and ran 425.17 seconds, exiting 1 (`repairs/continuation01_1792383980211787588/continuation01_1792383980211787588.result.json:3-13`). The next boundary still found the foundation ineligible.
- Assisted continuation 2 is also explicitly marked assisted and ran 520.31 seconds, exiting 1 (`repairs/continuation01_1792385688342176600/continuation01_1792385688342176600.result.json:3-13`). It added routes, controllers, and views, but did not resolve the failures below. These runtimes are recorded per run and are not attributed causally to either nudge. All post-continuation findings are assisted outcomes. The allowed two nudges have now been consumed; no further assistance file was created.

## Current assisted foundation review

The submission remains seriously incomplete and internally inconsistent:

- Git hygiene is absent: `git rev-list --all --count` and `git ls-files | wc -l` both return 0; all 23 top-level status entries are untracked. Both captured repair `gitlog.txt` files are empty.
- The only quick test-environment check, `bin/rails test`, exits 1 during `test:prepare` because `app/assets/tailwind/application.css` is absent. No test executes. There are zero `*_test.rb` files and no `test/system` directory; `test/final_checks.rb` is not a Rails test and is itself syntax-invalid at its constant-named keyword parameters (`project/test/final_checks.rb:15-18`).
- `ChatAdapter` is syntax-invalid at the provider call and forwarding placeholders (`project/app/services/chat_adapter.rb:14-23`, `:74-80`). Static `ruby -c` confirms both this file and `test/final_checks.rb` fail parsing.
- The database cannot migrate as written: the users migration indexes an uncreated `reset_password_sent_at` column (`project/db/migrate/20261017115000_devise_create_users.rb:3-19`); the chat migration adds `chats.user_id` although it creates `owner_id`, and duplicates the automatically-created message index (`project/db/migrate/20261017120000_create_chats_and_messages.rb:3-20`); the later index migration only adds a message-state index when that column is absent, the inverse of the required guard (`project/db/migrate/20261017120200_add_chat_indexes.rb:3-7`).
- Associations and queries disagree with the schema. `User#chats` defaults to `user_id`, while `Chat` belongs through `owner_id`; `Chat.owned_by` also queries nonexistent `user_id` (`project/app/models/user.rb:9-11`; `project/app/models/chat.rb:2-15`).
- Authentication is not viable: the model enables Devise modules but defines no Devise routes, while the custom session controller calls undefined `User.authenticate` (`project/app/models/user.rb:1-8`; `project/app/controllers/sessions_controller.rb:10-21`). Routes also define duplicate named helpers for login and logout (`project/config/routes.rb:4-7`), and views call undefined `post_login_path` (`project/app/views/sessions/new.html.erb:13`).
- The chat flow calls undefined `ChatAssistant` constants (`project/app/services/chat_service.rb:19-23`; `project/app/services/open_router_adapter.rb:18-21`), renders a nonexistent `_show` partial (`project/app/controllers/chats_controller.rb:9-11`), and provides an empty `app/javascript` directory rather than a Hotwire/Stimulus implementation. No Compose file exists. The README remains the generated placeholder (`project/README.md:1-24`).
- The Dockerfile is only the generated production image and references a `ruby:4.0.7-slim` base (`project/Dockerfile:10-12`); no image build was attempted, per the static-only procedure.

These are systemic application, schema, test, UI, documentation, and delivery failures, not an ordinary minor defect. The app cannot support fair sprint-02 evolution or later routed/live sabotage verification.

## Transcript-input contamination and isolation

- Original-sprint and both assisted-continuation tool **inputs** were scanned; incidental outputs were not counted as reads. No successful input read a sibling generated app, v4 sabotage/grading material, success report, rubric, or shield directory. Dependency-source reads were permitted by the sprint prompt.
- Assisted continuation 1 deliberately listed `/` (`repairs/continuation01_1792383980211787588/continuation01_1792383980211787588.ndjson:415`). Assisted continuation 2 attempted edits against two malformed sibling-like result paths; both operations failed with file-not-found (`repairs/continuation01_1792385688342176600/continuation01_1792385688342176600.ndjson:220`, `:396`). It also successfully wrote candidate-generated files to three malformed adjacent result paths rather than the target project (`:306`, `:324`, `:456`). Those out-of-scope paths were not inspected or modified during this review. This is an isolation/targeting failure, although it does not establish grading-key or sibling-source contamination.

## Injection manifest and boundary verdict

The machine-readable `injection-manifest.json` records all 14 items, weights, boundary status, and evidence. Items #1–#14 are `not_scheduled`; boundary-applied count is 0. Severity totals are Critical 10, High 21, Medium 8, Low 1, denominator **40**. Item #3 remains the Devise 4.7.0 variant at weight 3 because the app selected Devise; the current lock is 4.9.4 (`project/Gemfile:21`; `project/Gemfile.lock:109`).

Required sprint-01 zero-injection accounting is complete, but `eligible=false`: two assisted continuations did not yield a runnable, tested, committed foundation, and the latest continuation also breached target isolation. Runtime behavior beyond the first test-preparation failure remains unknown and was not inferred.
