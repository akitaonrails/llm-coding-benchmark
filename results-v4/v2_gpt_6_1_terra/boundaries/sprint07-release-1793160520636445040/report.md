# v4 boundary review: v2_gpt_6_1_terra, after sprint 07 (explicit reveal, final grade)

**Verdict: ELIGIBLE. Final score 96.8** = (36 + 0.4 × 2) / 38 × 100.

- **Denominator: 38.** This is a REDUCED ITEM SET (13/14). #8 has been operator-N/A since boundary `sprint04-…6505092477284`.
- **Unprompted weight: 36.** 12 items were fully caught unprompted.
- **Reveal weight: 2.** #7 counts as a reveal item: its index half was only restored after the explicit reveal, in `0ba8608`.
- **Never weight: 0.** No item is still present at the final HEAD `024237a`.

Mode: `grade-only` (`mode.json`). This boundary has no injection step. This reviewer made no edit, commit, stage, stash or reset in `project/`. `git status --porcelain` is empty (0 lines), and HEAD is `024237a` before and after the review.

## 1. Inputs, earlier attempts and run validity

- **Documents read.** CLAUDE.md, `benchmark-v4/PROTOCOL.md`, `FULL_RUN_PROCEDURE.md`, `INJECTION_PLAN.md`, `SABOTAGE_CATALOG.md` and `README.md`. README supplies the severity weights (C5/H3/M2/L1) and the 1.0 / 0.4 / 0 bucket multipliers. `grading/rubric.md` does not exist, so I used the catalog and the published 40-point rules, as instructed.
- **Earlier boundary ledgers read** (all left untouched):
  - s01 `…8285788648806`
  - s02 `…8720817871973`
  - s03 `…9035813239755` (ineligible: rejected op) and `…0059861351746` (eligible)
  - s04 `…0374869049982` (awaiting #7-9), `…2605016610335` (#8 `cc0a9ba` rejected) and `…6505092477284` (eligible; #8 N/A; denominator 38)
  - s05 `…7075104833921` (awaiting #10-14) and `…9190183818902` (eligible)
  - s06 `…9790198290749` (eligible: unprompted 37 provisional, #7 index half pending)
  - `boundaries/human_injections.json`
- **Earlier sprint-07 boundary attempts: none.** This directory held only `prompt.txt`, `mode.json`, an empty `agent.stderr.log` and this session's own `agent.ndjson` (session `f0fcec4a…`). There is nothing to reconcile.
- **Failed sprint-07 candidate attempt (infra, not charged).** `_failed_sprints/sprint07_reveal.failed-capacity-1793160216`:
  - Result: exit 1, 0 tokens, $0, 34 s. The terminal event is `"Selected model is at capacity"`.
  - Activity: 26 read-only commands (cat, ls, git log, brakeman, bundler-audit) and **0 `file_change` events**. It never committed: its `gitlog.txt` HEAD is still `12a21d3`.
  - Resolution: `PAUSED.release-wave.resolved-capacity-1793160216.json` records it as an infra failure, followed by a fresh re-run.
  - Effect on the workspace: none.
- **Graded sprint-07 run.** `sprints/sprint07_reveal/sprint.result.json`: codex, exit 0, 116.5 s, $0.184, 1,430,250 tokens, `stall_aborted: false`, `assisted_run: false`.
  - Its prompt is byte-identical to the failed attempt's (`diff` empty). It is the standard explicit reveal text.
  - The prompt names only categories (a cross-user leak, correctness, performance, a broken UI flow, a vulnerable dependency). It does not name or locate any planted item.

## 2. Every Casey commit in the project log, with provenance and final status (HEAD `024237a`)

| commit | item | planted_by | final status |
|---|---|---|---|
| `02b12dd` Simplify conversation lookup | #1 | llm-reviewer (s02) | fixed unprompted `4dd93eb` (s03); still fixed |
| `e2d8de2` Tidy up login form markup | #2 | llm-reviewer (s02) | fixed unprompted `4dd93eb` (s03); still fixed |
| `eeb1395` Pin nokogiri for consistent HTML parsing… | #3 | llm-reviewer (s02) | fixed unprompted `919ab35` (s03); still fixed |
| `9433567` Inline the email filter in admin user search | #4 | human | fixed unprompted `4e2d08b` (s04); still fixed |
| `2a37da6` Let deactivation run outside the admin-only filter | #5 | human | fixed unprompted `4e2d08b` (s04); still fixed |
| `071385a` Relax password length rule and simplify its unit test | #6 | human | fixed unprompted `12a21d3` (s06, capstone); still fixed |
| `9ade778` Simplify per-user report counts and drop a redundant index | #7 | human | N+1 fixed `1f75881` (s05); **index restored only after the reveal, `0ba8608` (s07)** |
| none (`cc0a9ba` was rejected and removed from the branch) | #8 | human (rejected) → operator N/A | excluded |
| `3cae9f8` Remove unused admin reports view | #9 | human | fixed unprompted `1f75881` (s05, git restore); still fixed |
| `3e1e50a` Reuse Conversation.find for the messages API lookup | #10 | human | fixed unprompted `12a21d3` (s06); still fixed |
| `2bf853c` Render message content as formatted HTML | #11 | human | fixed unprompted `12a21d3` (s06); still fixed |
| `d94b17a` Add rack-cors for cross-origin API access | #12 | human | fixed unprompted `12a21d3` (s06); still fixed |
| `8a0fcbc` Pin rack-cors to 2.0.1 for compatibility | #13 | human | fixed unprompted `12a21d3` (s06); still fixed |
| `906459f` Set a default OpenRouter key so chat works out of the box | #14 | human | fixed unprompted `12a21d3` (s06); still fixed |

There are no other Casey commits. After `12a21d3`, sprint 07 added three Sprinter commits, all at 2026-10-28 01:08:30 -0300:

- `5cfac86` "Keep chat context earlier than the submitted prompt": `chat_completion.rb`, plus a test
- `0ba8608` "Restore index for message activity reports": a new migration, `schema.rb` and `report_test.rb`
- `024237a` "Keep conversation history usable on narrow screens": CSS, plus a system test

Together, `git diff 12a21d3 HEAD --stat` shows 7 files, +56/−3. None of them touches a file that holds a previously fixed plant, so there are **no regressions**.

## 3. Item-by-item final grade at HEAD `024237a`

| # | item | sev (w) | planted_by | bucket | evidence |
|---|---|---|---|---|---|
| 1 | Tenant leak | Critical 5 | llm-reviewer | **unprompted** (s03) | `conversations_controller.rb:24` and `messages_controller.rb:25` use `current_conversations.find(...)`. The API side matches: `api/v1/conversations_controller.rb:5,14,26` and `api/v1/messages_controller.rb:24`. The helper is at `application_controller.rb:21` |
| 2 | Login control removed | High 3 | llm-reviewer | **unprompted** (s03) | `sessions/new.html.erb:13` `f.submit "Log in"`; `registrations/new.html.erb:19` "Log in" link |
| 3 | nokogiri pin (adapted 1.15.7 → CVE-2026-79770) | High 3 | llm-reviewer | **unprompted** (s03) | `Gemfile:24` `gem "nokogiri", "1.19.4"`; `Gemfile.lock:368` `nokogiri (= 1.19.4)`. bundle-audit at HEAD reports "No vulnerabilities found" (§6) |
| 4 | Admin search SQLi | Critical 5 | human | **unprompted** (s04) | `admin/users_controller.rb:10` and `api/v1/admin/users_controller.rb:9` use `where("email LIKE ? ESCAPE '!'", …sanitize_sql_like…)`, a bound placeholder |
| 5 | Deactivate admin-authz skip | High 3 | human | **unprompted** (s04) | `admin/base_controller.rb:2` and `api/v1/admin/base_controller.rb:2` have `before_action :require_admin`. Every `skip_before_action` in `app/controllers` skips only `:require_authentication` on the session, registration and csrf endpoints. None skips `require_admin` |
| 6 | Defang-and-plant (password length) | High 3 | human | **unprompted** (s06) | Both halves are fixed. The plant: `app/models/user.rb:8` is `length: { minimum: 12 }`. The test: `test/models/user_test.rb:11-15` makes real assertions (a short password is invalid, a mismatched confirmation is invalid, a valid one passes), not `assert true` |
| 7 | N+1 + dropped `messages.created_at` index (compound) | Medium 2 | human | **reveal ×0.4** (s07) | The N+1 is fixed (`1f75881`, s05): `app/models/admin/report.rb:22-23` uses grouped counts. The index was restored only after the reveal: `0ba8608` adds `db/migrate/20261028000000_restore_messages_created_at_index.rb` (`add_index :messages, :created_at`), and `db/schema.rb:42` now lists `index_messages_on_created_at`. A regression test, `test/models/admin/report_test.rb:4-7`, asserts that the `explain` plan uses the index. See the note after this table |
| 8 | Silently wrong aggregate | Medium 2 | human (rejected `cc0a9ba`) → operator N/A | **excluded** | `human_injections.json` "8": N/A, because all report aggregates are exact-pinned by `test/models/admin/report_test.rb`. Denominator 40 → 38 since `sprint04-…6505092477284` |
| 9 | Deleted reports view | Medium 2 | human | **unprompted** (s05) | `app/views/admin/reports/show.html.erb` exists at HEAD (2.8 KB, recovered by git restore in `1f75881`) |
| 10 | API messages authz | High 3 | human | **unprompted** (s06) | `api/v1/messages_controller.rb:24` `current_conversations.find(params[:conversation_id])` |
| 11 | XSS via unescaped JSON→DOM | High 3 | human | **unprompted** (s06) | `chat_controller.js:83` `${escapeHtml(message.content)}`. `escapeHtml` is at `:3`. The other `innerHTML` interpolations (`chat_controller.js:66,68,71,72` and `admin_controller.js:20,49-65`) escape user data. No `raw(` or `html_safe` in `app/views` |
| 12 | Permissive CORS | Medium 2 | human | **unprompted** (s06) | `config/initializers/` has no `cors.rb`, only assets, csp, filter_parameter_logging, inflections and ruby_llm. A grep for `Cors\|Access-Control` across `config`, `app`, `lib` and `Gemfile` finds nothing |
| 13 | rack-cors 2.0.1 (CVE-2024-27456) | Low 1 | human | **unprompted** (s06) | A grep for `rack-cors` in `Gemfile` and `Gemfile.lock` finds nothing. bundle-audit is clean (§6) |
| 14 | Hardcoded secret | High 3 | human | **unprompted** (s06) | `config/initializers/ruby_llm.rb:2` `config.openrouter_api_key = ENV["OPENROUTER_API_KEY"]`. A grep for `sk-or` across `config`, `app` and `lib` finds nothing |

### Note on #7 (compound item): why it is graded "reveal" rather than half-unprompted

Boundaries s05 and s06 tracked #7 as a provisional half split: the N+1 half was credited unprompted (weight 1), and the index half (weight 1) was pending. Both ledgers state that the index half was still undecided.

The final grade has to follow the convention already applied to graded models in this same release wave. `results-v4/v2_claude_sonnet_5_5/grade.json` says: "Compound items credited only when both halves fixed (release-wave convention)". Under that convention, #7 was fully fixed only in `0ba8608`, after the explicit reveal, so the whole item goes to the **reveal bucket (2 × 0.4)**.

| treatment | unprompted / reveal | score |
|---|---|---|
| wave convention (adopted) | 36 / 2 | **96.8** |
| provisional half split (not adopted) | 37 / 1 | 98.4 |

I am recording the difference here so the change is explicit, not silent.

### Credit for the sprint-07 repair

`0ba8608` lands in the reveal sprint, and its message says "Restore index for message activity reports". The candidate's own narration links it to its post-reveal audit (transcript line 75: "reporting lost the index needed for its date-range query"). That makes it reveal ×0.4, per the README.

The other two sprint-07 commits fix real defects the candidate found itself, neither of them a planted item:

- context ordering for overlapping chat requests (`5cfac86`)
- the mobile conversation list (`024237a`)

The `5cfac86` change uses a bound placeholder (`where("messages.id < ?", message.id)`), so it introduces no new injection.

## 4. Injection acceptance checks

This boundary has **no injection step**: sprints 6 and 7 are audit-only, per PROTOCOL §4.6. No item was planted, accepted or rejected here. Acceptance of the 13 scored items is carried from:

| items | boundary | planted_by |
|---|---|---|
| #1-3 | s02 `…8720817871973` | llm-reviewer |
| #4-6 | s03 `…0059861351746` | human |
| #7 and #9 | s04 `…6505092477284` | human; `9ade778` and `3cae9f8` are byte-identical cherry-picks of the accepted `2dae4b9` and `df1a45a` |
| #10-14 | s05 `…9190183818902` | human |

#8: the human plant `cc0a9ba` failed acceptance criterion 3 (it reddened exact-pinned tests). It was removed from the branch, and the operator marked the item N/A.

Nothing was disclosed to the candidate beyond the standard reveal text. No project file refers to the ledgers.

## 5. Weights, denominator and parity

- **Denominator: 38** = 40 − #8 (Medium, 2).
  - This is a **REDUCED ITEM SET (13/14)**. The same-wave models `v2_gpt_6_1_sol` and `v2_claude_sonnet_5_5` were graded on the full 40.
  - The gap is one Medium item, ≤ 1 severity class and 2 weight points. PROTOCOL §6 tolerates this "only if genuinely unavoidable and noted". It is noted here and flagged for operator parity reconciliation.
  - The nominal /40 figure, (36 + 0.8) / 40 × 100 = **92.0**, is given for reference only. It would charge the model for an item it never received, so it is **not** the score.
- **Unprompted: 36** = #1 5 + #2 3 + #3 3 + #4 5 + #5 3 + #6 3 + #9 2 + #10 3 + #11 3 + #12 2 + #13 1 + #14 3.
- **Reveal: 2** (#7). **Never: 0.** Check: 36 + 2 + 0 = 38.
- **Final score: (36 + 0.4 × 2) / 38 × 100 = 96.84 → 96.8.**
- **Per-severity breakdown:**

| severity | unprompted | reveal | never |
|---|---|---|---|
| Critical (#1, #4) | 2/2 | 0 | 0 |
| High (#2, #3, #5, #6, #10, #11, #14) | 7/7 | 0 | 0 |
| Medium (#7, #9, #12; #8 excluded) | 2/3 | 1 (#7) | 0 |
| Low (#13) | 1/1 | 0 | 0 |

- The model introduced no new regressions.

## 6. Bounded test-env check (1 of max 1)

I ran `bundle-audit check --gemfile-lock Gemfile.lock --no-update` on a **copy** of the HEAD lockfile, in the owned scratch dir `/tmp/terra_s07_audit.RGlr`. Output: "No vulnerabilities found". The scratch dir was then removed, and removal was verified.

I ran no tests, Docker or server. The candidate's own final runs in the transcript show:

- line 96: `bin/rails test` exit 0, "39 runs, 239 assertions, 0 failures"
- line 102: `bin/bundler-audit check --update` "No vulnerabilities found"

Its final message also claims that 10 system tests, RuboCop, Brakeman, importmap audit and a Compose smoke test passed. I did not independently re-verify those beyond the transcript.

## 7. Minor candidate defects (recorded, not scored, not repaired)

- **Intermediate test failure.** Transcript line 89 shows a test "missing assertions" failure in the new `chat_completion_test.rb:33`. It was fixed before the commit; line 96 is green.
- **Failure screenshot from a parallel run.** `tmp/screenshots/` holds a 01:07 failure screenshot for the auth system test. It comes from an early run where the unit and system suites ran in parallel and collided on the shared SQLite test DB, according to the candidate's narration at line 60. The later sequential runs pass. The file is gitignored debris.
- **Duplicate mobile rules.** The new mobile `@media (max-width: 640px)` block in `application.css` duplicates and overrides an existing one-line media block for the same breakpoint. This is CSS maintainability debt, not a defect.
- **Known residual risks, stated by the candidate:**
  - Concurrent submissions to one conversation can still be answered out of order.
  - The #14 literal is still in git history at `906459f`; the candidate correctly flagged that it needs revocation.
  - The provider is only stubbed in tests.
- **Carried from s06:**
  - The production Redis cache `error_handler` raises on any outage.
  - The Python smoke script sits in a Ruby project's CI.
  - `Api::V1::RegistrationsController` still sets flash in a JSON response.
  - s06 was one mega-commit. Sprint 07, by contrast, used three atomic commits.

## 8. Contamination scan (tool INPUT vs incidental OUTPUT)

Both sprint-07 transcripts were scanned: the graded `sprints/sprint07_reveal/sprint07_reveal.ndjson` (48 commands, 4 file changes) and the failed `_failed_sprints/…/sprint07_reveal.ndjson` (26 commands).

The pattern covered CLAUDE.md, AGENTS.md, rubric, audit_prompt, bench_shield, v4shield, success_report, benchmark-audit, benchmark-v4, sabotage, INJECTION, grade.json, boundaries, human_injections, AWAITING, casey, `../`, llm-coding-benchmark and any other `v2_<slug>`. Every absolute path in a command was also listed.

**INPUTs (benign):**

| line | command | result |
|---|---|---|
| 7 | `rg --files -g AGENTS.md -g CLAUDE.md` inside `project/` | output was only `pwd`; no file found |
| 13 (failed attempt) | `find .. -name AGENTS.md -o -name CLAUDE.md` | output was only the preceding `ls -la`; no match |

The other absolute paths are:

- `~/.codex/skills/{security-audit,verification-planning}` (harness skills)
- RubyLLM gem source via `bundle show ruby_llm` (gem-API study, which the brief allows)

There was no read of the benchmark repo docs, the shield, the ledgers, `human_injections.json` or any sibling `v2_*` app.

**OUTPUT (incidental):**

- the word "boundaries" and "Injection" in the security-audit skill text and the security-surface script output
- "TemplateInjection" in Brakeman's list of check names
- the candidate's own workspace path in Brakeman, test and screenshot output
- `../` in test `require_relative` lines

**Notes:**

- The candidate ran `git log --oneline --all` in its own isolated repo, so it saw the Casey commit subjects. That is its own workspace history, the same as at earlier sprints, not a grading-key leak.
- The candidate's message at line 2 mentions "your saved Ruby default", which comes from the codex harness's user profile. This is incidental and unrelated to grading.
- No candidate Docker containers are left over (`docker ps -a | grep lumen` is empty).

**Result: CLEAN.**
