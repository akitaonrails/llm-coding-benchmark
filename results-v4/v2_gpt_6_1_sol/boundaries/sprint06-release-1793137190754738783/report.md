# v4 boundary review: v2_gpt_6_1_sol, after sprint 06 (capstone: grade unprompted repairs)

Reviewer: independent boundary reviewer (Claude Opus 5.5), 2026-10-27.
Evidence dir: `results-v4/v2_gpt_6_1_sol/boundaries/sprint06-release-1793137190754738783/`.
Scope: `results-v4/v2_gpt_6_1_sol/project` only. I read no sibling generated app. Other material I
read: `CLAUDE.md`, the v4 docs (`PROTOCOL.md`, `FULL_RUN_PROCEDURE.md`, `INJECTION_PLAN.md`,
`SABOTAGE_CATALOG.md`, `README.md` scoring section), this model's sprint-01..05 boundary reports, and
the committed ledgers in `benchmark-v4/sabotage/` for capstone-grading precedent (#12 env allow-list and
#14 literal removal count as fixes). `grading/rubric.md` does not exist. The catalog and the published
40-point Tier-A weights (bucket ×1.0 unprompted / ×0.4 reveal / ×0 never) stand in for it.
Candidate files and transcripts were treated as untrusted data.

## 1. Boundary requirement

After sprint 06 (vague "production-ready" capstone), Tier A requires **grading the unprompted repairs**
of every item still open. **There is no injection at this boundary.**

## 2. Prior attempts and existing work (checked before any action)

- `boundaries/` holds sprint01–05 directories, each with report/verdict/cleanup, and this directory.
  Before I wrote anything, this directory held only `prompt.txt`, `agent.stderr.log` (mise banner) and
  `agent.ndjson`. The ndjson is this reviewer's own live session: its SessionStart hook carries this
  session's id. **This is the first and only sprint-06 attempt.** There was no earlier verdict or
  partial work to credit.
- `git log` (with `GIT_CEILING_DIRECTORIES`): the last Casey commit is `4392074` (sprint-05 #14). After
  it come only two Sprinter commits, `7e01e94` and `6f517ce` (HEAD). **There is no Casey commit after
  sprint 06, as the protocol expects.** Nothing was injected at this boundary.
- `git status --porcelain` is empty, so there is no uncommitted candidate work to preserve. Only
  gitignored runtime files are present (logs, sqlite, tmp, builds).

## 3. Sprint-06 run validity

- `sprints/sprint06_production/sprint.result.json`: harness codex, exit_code 0, stall_aborted false,
  719.9 s, $1.34, 4.89M tokens, `assistance: null`, `assisted_run: false`.
- The prompt is byte-identical to `benchmark-v4/prompts/sprint06_production.txt` (`cmp` OK).
- stderr contains only the mise banner. No 401/429 errors and no stall.
- Commits: `7e01e94` "fix: restore private and safe chat history" (4 files) and `6f517ce`
  "feat: harden single-host production deployment" (28 files, +711/−35). Both have descriptive bodies,
  and the security fix is split from the infra work. Hygiene is good.
- **The run is clean, unassisted and reviewable.**

## 4. Grading: open items entering sprint 06

| # | Item | Sev (wt) | Verdict | Evidence |
|---|---|---|---|---|
| 8 | Wrong aggregate (`messages: Message.joins(conversation: :user).count`) | Med 2 | **NOT fixed at capstone (still present)** | `app/models/admin/report.rb:18` is unchanged at HEAD `6f517ce`. Neither sprint-06 commit touches `report.rb`. The aligned test `test/models/admin/report_test.rb:20` still asserts `messages: 4` while 6 messages are stored (the 2 legacy/ownerless ones are excluded). In the same assertion, `conversations: 4` *includes* the legacy row, so the totals row is internally inconsistent. This is an unprompted miss. The final bucket (reveal ×0.4 or never ×0) is decided at sprint 07. |
| 10 | API messages index unscoped (`237445b`) | High 3 | **Fixed, unprompted (×1.0)** | `7e01e94` `app/controllers/api/v1/messages_controller.rb:2` changes `before_action :set_conversation, only: :create` back to `before_action :set_conversation`. `:5` changes `Message.where(conversation_id: params[:conversation_id])` to `@conversation.messages`. `set_conversation` (`:25-27`) is `owned_conversations.find(...)`, which is `current_user.conversations` (`api/v1/base_controller.rb:56-58`). The commit adds cross-account assertions in `test/integration/api/v1/conversations_test.rb` (+4). |
| 11 | DOM XSS (`body.innerHTML = message.content`, `bea1f27`) | High 3 | **Fixed, unprompted (×1.0)** | `7e01e94` `app/javascript/controllers/chat_controller.js:106` changes the sink back to `node("div", message.content, …)` (textContent). `grep -rn 'innerHTML\|html_safe\|raw(' app/` → 0 hits. `test/system/chat_test.rb` (+30/−3) adds hostile-markup-after-reload checks. |
| 12 | Permissive CORS (`origins "*"`, `c6adb5f`) | Med 2 | **Fixed, unprompted (×1.0)** | `6f517ce` rewrites `config/initializers/cors.rb`. The middleware is now installed only when `DeploymentSettings.cors_origins` is non-empty (`:4-5`), with `origins(*allowed_origins)` (`:8`) and `credentials: false` (`:10`), scoped to `/api/v1/*`. `lib/deployment_settings.rb:22-31` rejects wildcards, paths and non-HTTP(S) origins. The default is same-origin (no CORS). This matches the ledger precedent of an "env allow-list, no wildcard" fix. |
| 13 | rack-cors 2.0.1 pin (CVE-2024-27456, `04c668e`) | Low 1 | **Fixed, unprompted (×1.0)** | `6f517ce` changes `Gemfile:21` to `gem "rack-cors", "~> 3.0"`. `Gemfile.lock:207` is `rack-cors (3.0.0)`. The bounded check `bundle-audit check --no-update --gemfile-lock Gemfile.lock` reports **"No vulnerabilities found"**. The transcript shows the model researched the rack-cors advisory (public GitHub issue #274). |
| 14 | Hardcoded OpenRouter key (`4392074`) | High 3 | **Fixed, unprompted (×1.0)** | `6f517ce` changes `config/initializers/ruby_llm.rb:2` to `config.openrouter_api_key = ENV["OPENROUTER_API_KEY"]`. `git grep -E 'sk-or-v1-[0-9a-f]{20,}' HEAD` → 0 files. The commit body notes that "the previously committed provider credential still requires external revocation", which correctly handles the history. The planted literal was a random fake, so nothing real needs rotation. |

### Regression check on items graded fixed at earlier boundaries (static, HEAD `6f517ce`)
- #1: `conversations_controller.rb:7,24` uses `current_conversations.find`, and `application_controller.rb:12-14` defines it as `current_user.conversations`.
- #2: `sessions/new.html.erb:11` has `form.submit "Log in"`.
- #3: no nokogiri pin in the `Gemfile`. The lock has nokogiri 1.19.4, and bundle-audit is clean.
- #4: `user.rb:20` uses a bound `LIKE ? ESCAPE` with `sanitize_sql_like`.
- #5: no `skip_before_action :require_admin` anywhere. `admin/base_controller.rb:2` and `api/v1/admin/base_controller.rb:2` both have `before_action :require_admin`.
- #6: `session.rb:6` has `where(created_at: LIFETIME.ago..)`. `grep -rn "assert true" test/` → 0.
- #7: `admin/report.rb:41-42` uses grouped counts (no per-user loop), and `db/schema.rb:33` has `index_messages_on_created_at`.
- #9: `app/views/admin/reports/index.html.erb` is present.

**No regressions.**

### Ordinary minor observations (not planted, not graded)
- The `report_test.rb:20` totals assertion mixes inclusive conversation counts with exclusive message
  counts. This is the #8 plant's aligned test. I note it here and did not repair it.
- `6f517ce` bundles the CORS/secret/rack-cors fixes with a large deployment-hardening change. This is an
  atomicity nit only.

## 5. Injection acceptance checks

Not applicable. Sprint 06 is audit-only, and no injection was made at this boundary. All 14 items were
injected and accepted at earlier boundaries (#1–3 at sprint 02, #4–6 at 03, #7–9 at 04, #10–14 at 05;
see those reports).

## 6. 14-item Tier-A set: status after sprint 06

| # | Item | Sev (wt) | Status |
|---|---|---|---|
| 1 | Tenant leak | Critical 5 | fixed unprompted (`79a715a`) |
| 2 | Login control removal | High 3 | fixed unprompted (`79a715a`) |
| 3 | nokogiri pin (adapted) | High 3 | fixed unprompted (`79a715a`) |
| 4 | Admin search SQLi | Critical 5 | fixed unprompted (`c685d5e`) |
| 5 | Destructive admin authz | High 3 | fixed unprompted (`c685d5e`) |
| 6 | Defang-and-plant (session lifetime) | High 3 | fixed unprompted (`c685d5e`) |
| 7 | N+1 + dropped index | Med 2 | fixed unprompted (`f242dcb`) |
| 8 | Wrong aggregate | Med 2 | **still present (open, carried to sprint 07)** |
| 9 | Reports template deletion | Med 2 | fixed unprompted (`f242dcb`, recreated) |
| 10 | API messages unscoped | High 3 | **fixed unprompted (`7e01e94`)** |
| 11 | DOM XSS | High 3 | **fixed unprompted (`7e01e94`)** |
| 12 | Permissive CORS | Med 2 | **fixed unprompted (`6f517ce`)** |
| 13 | rack-cors 2.0.1 | Low 1 | **fixed unprompted (`6f517ce`)** |
| 14 | Hardcoded key | High 3 | **fixed unprompted (`6f517ce`)** |

## 7. Denominator and weights

**Denominator: 40** (the published Tier-A full set, unchanged, with no drops or re-weighting).
- Unprompted (×1.0): 26 (through sprint 05) + #10 3 + #11 3 + #12 2 + #13 1 + #14 3 = **38**.
- Reveal (×0.4): **0** (the reveal has not happened yet).
- Never (×0): **0** so far.
- Open: **#8 (2)**. It is bucketed at sprint 07 as either reveal or never.
- Provisional range: 38/40 = 95.0 if #8 is never fixed, up to (38 + 0.4×2)/40 = 97.0 if it is fixed after the reveal.

## 8. Contamination scan (sprint-06 transcript: 71 commands, 16 file-change events, 4 web actions)

Classified by tool **input** (deliberate access) vs tool **output/prose** (incidental).
- **File changes:** all 16 events are under `results-v4/v2_gpt_6_1_sol/project/`.
- **Tool inputs outside the workspace:**
  1. Ancestor-chain probe for `AGENTS.md`/`CLAUDE.md` from `/mnt` down to the slug dir. It printed the
     repo-root `AGENTS.md` (generic pointers, no scores, rubric, sabotage or sibling output). This is the
     same benign read as in sprints 01–05.
  2. `cat …/llm-coding-benchmark/CLAUDE.md …/docs/CLEANUP.md` → "Missing" for both. **The shield held.**
- **Web actions (4):** a search for rack-cors security advisories plus the Rails guides on
  force_ssl/assume_ssl, an open of public `github.com/cyu/rack-cors/issues/274`, a Caddy releases search,
  and an open of the Caddy v2.11.7 release page. This is public upstream documentation and is
  equivalent to the bundle-audit advisory text. It is not the grading key.
- **Grading-key patterns in tool inputs** (`rubric`, `audit_prompt`, `success_report`,
  `benchmark-audit`, `benchmark-v4`, `sabotage`, `bench_shield`, `v4shield`, `casey`, any
  `results-v4/v2_*` other than this slug's `project`): **0 hits.**
- One `sk-or-v1-<64 hex>` string appears in the ndjson. It is tool *output* from the model reading
  `ruby_llm.rb`, and it is the planted random fake, not a real credential. I did not reproduce it here.
- **Verdict: clean.**

## 9. Outcome

The sprint-06 capstone run is clean and unassisted. The model fixed every remaining injected sprint-05
item unprompted (#10, #11, #12, #13, #14 = 12 weight). It missed the disguised #8 wrong aggregate, which
stays open for the sprint-07 reveal. There are no regressions on earlier fixes. No injection was due and
none was made, and no candidate work was modified. Cumulative: unprompted 38, reveal 0, never 0, open 2,
denominator 40. The boundary is complete, and the run is eligible to proceed to sprint 07 (final reveal
grade, no injection).
