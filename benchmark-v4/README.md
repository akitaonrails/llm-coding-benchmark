# v4 — "The Sprint": an evolving RubyLLM Rails project with malicious teammates

**Status: in construction (2026-09-06).** This REPLACES the synthetic stdlib v3
(tasks 10–18), which drifted away from the "grounded in day-to-day reality" mandate into
isolated snippets. The synthetic v3 ecosystem *data* is kept as a reference appendix
(`docs/success_report.v3.md`), but it is not the benchmark going forward.

## The idea

One **cohesive, real Rails application** (real framework, real gems, real DB, frontend +
backend + docker/infra) that a model **evolves feature-by-feature across sequential
sprints in a single accumulating workspace** — exactly like real project work, and like
v2, but as a *project over time*.

Between sprints, a **malicious or careless "teammate" commits code into the same repo**
(the SAME injection for every model — fair and comparable): **CVE-class vulnerabilities**
and subtle sabotage.

**Core principle — never name the sabotage.** We do NOT tell the model "a teammate added
malicious code, review and fix it." That would give away the game. Instead every prompt is
framed naturally so that a *diligent* engineer has a legitimate **opening to check** and
would discover the planted bugs on their own — while a sloppy one builds right over them.
The whole benchmark is a test of **unprompted vigilance**. The only lever that varies
across sprints is how much of a natural opening the framing gives:

- **No opening** — "add feature X." (Pure vigilance: does it audit code it's building on?)
- **Soft opening** — "we merged some teammate PRs recently; continue with feature X" or
  "get familiar with the codebase, then add X." (A natural reason to look around — never a
  statement that something is wrong.)
- **Vague capstone** — "prepare this for production; make sure it's production-ready."
  (Maximum opening, still no mention of sabotage — the last chance to catch everything
  before shipping.)

## Standard sprint preamble (in every sprint prompt)

Every sprint prompt carries the same realistic baseline expectation — this is NOT a hint
about sabotage; it's ordinary project hygiene, and it makes the test-discipline/vigilance
grading *fair* (a model that skips tests and ships a broken flow is failing an explicit,
reasonable instruction it was given up front):

> Follow proper Ruby on Rails best practices throughout. Write proper automated tests —
> **unit/model tests AND system/feature (Capybara) tests for user-facing flows** — and keep
> them green. Keep the code secure and idiomatic (strong params, scoped queries,
> authorization, migrations with indexes, no N+1), keep RuboCop/Brakeman/bundle-audit
> clean, and keep the app runnable. Use git: commit your work at the end of each task with
> clear, atomic, well-described commits.

This mirrors the v2 brief ("Add proper Minitest unit tests… follow proper Rails best
practices… Brakeman, RuboCop, bundle-audit"). It legitimizes grading test discipline,
security hygiene, and commit quality — all things the model was explicitly asked to do.

## Base app

Evolve the **v2 RubyLLM chat app** (Rails 8 + Hotwire/Turbo + Tailwind + RubyLLM →
OpenRouter, Minitest, Dockerfile/compose) — see `prompts/benchmark_prompt_v2.txt`.

## The sprint arc (features build on each other)

1. **Foundation** — the base RubyLLM chat app (as v2).
2. **Multi-user** — authentication + users own their conversations (associations,
   migrations, sessions).
3. **Admin** — an admin area to manage users (roles, authorization).
4. **Reports** (DB-heavy) — dashboards over users × conversations × messages. This is where
   SQL quality is scrutinized: **N+1 avoidance, proper indexes, joins/includes,
   parameterized queries**.
5. **API refactor** — refactor the backend to expose explicit **GraphQL (or public REST)
   APIs** the frontend consumes, detaching frontend from backend (a real refactoring phase
   that raises DB/contract complexity).
6. **Production deploy (vague capstone)** — "prepare this project for production
   deployment; finish the Docker/compose setup and make sure it's production-ready."
   Silent — the real test is whether the model audits and finds the planted CVEs first.
7. **Explicit reveal (last chance)** — NOW we finally say it: "we deliberately injected a
   number of problems/vulnerabilities into this project over the sprints; this is your last
   chance to find and fix all of them before we deploy." This measures the *floor*: can the
   model fix the bugs even when explicitly told they exist?

### The three-tier vigilance profile (the key output)

For each planted bug, every model lands in exactly one bucket:
1. **Caught unprompted** — found & fixed during the build sprints or the vague capstone,
   with no one saying anything was wrong. (Best — real senior-dev vigilance.)
2. **Caught only after the explicit reveal** — untouched until sprint 7's explicit hint,
   then fixed. (Middle — capable but not vigilant.)
3. **Never fixed** — still present even after being explicitly told problems exist.
   (Worst — a capability gap, not just an attention gap.)

The per-model "vigilance profile" = the histogram across these three buckets over all
planted bugs. That is the headline v4 signal: *how many did it catch on its own, how
many only when told, and how many it couldn't fix at all.*

### Severity-weighted scoring (catching the BAD ones matters most)

Each planted bug carries a **severity weight** — resolving a critical data-leak counts far
more than tidying a low-severity nit, so a model can't look good by fixing only the easy
ones.

| severity | weight | examples |
|---|---|---|
| **Critical** | 5 | tenant-isolation / cross-user data leak, SQL injection, RCE (render path, deserialization), auth bypass |
| **High** | 3 | missing authorization / IDOR, command-injection gem (mini_magick), open redirect, GraphQL authz hole |
| **Medium** | 2 | N+1 / missing index, wrong aggregate, permissive CORS, DoS-class gem (nokogiri), file deletion |
| **Low** | 1 | insecure file perms (rack-cors 2.0.1), style/robustness nits |

**Bucket multiplier** (from the three-tier profile): caught unprompted = **1.0**, caught
only after the explicit reveal = **0.4**, never fixed = **0**.

**Vigilance score** = Σ(weight × bucket_multiplier) / Σ(weight) × 100 — so an unprompted
critical fix dominates, and never-fixing a critical is heavily penalized. We also report a
**per-severity breakdown** (of the criticals: how many unprompted / after-reveal / never;
same for high/medium/low), so "which models resolved the *severe* bugs vs only the minor
ones" is explicit. New regressions the model introduces count as negative.

## Per-sprint injection map (the concrete plan)

Same injection for every model. **Framing never names the sabotage** — "opening" =
how much of a natural reason-to-look the prompt gives (none / soft / vague), per the core
principle above.

| after sprint | injection | class | severity | opening | the test |
|---|---|---|---|---|---|
| 2 (multi-user) | remove user-scoping from a query (e.g. `Conversation.find(params[:id])` or `Conversation.all` instead of `current_user.conversations…`), so one user sees another's data | **broken access control / tenant-isolation leak** (OWASP #1) | **Critical (5)** | **none** | does it catch the cross-user data leak, or ship it to prod? |
| 3 (admin) | string-interpolated user search | SQL injection | **Critical (5)** | **soft** | vigilance given a natural reason to look |
| 3 (admin) | missing authorization on an admin action (no role check / `skip_before_action`) | broken authz / IDOR | **High (3)** | **soft** | " |
| 4 (reports) | N+1 query + missing index | performance | **Medium (2)** | **none** | SQL quality: N+1, indexes, joins/includes |
| 4 (reports) | subtle wrong aggregate (green-but-wrong) | correctness | **Medium (2)** | **none** | does it notice the wrong number? |
| 5 (API refactor) | GraphQL/REST authz hole | broken authz | **High (3)** | **soft** | authz on the new API surface |
| 5 (API refactor) | permissive CORS (`rack-cors` allow-all `*`) | CORS misconfig | **Medium (2)** | **soft** | " |
| 3+ | remove the login button/link from the view (users can't log in) | **functional/UI regression** (dumb, high-impact) | **High (3)** | **none** | do its system/feature tests catch it? does it ship a broken login? |
| 4+ | break a secondary link/label (minor) | functional/UI regression (dumb, low-impact) | **Low (1)** | **none** | test-coverage breadth |
| (any) | a "teammate" deletes an important file | availability / recovery | **Medium (2)** | **none/soft** | recover via `git restore`, not recreate |
| (build sprint) | pin `mini_magick 4.9.3` (CVE-2019-13574) | command-injection gem | **High (3)** | **none** | catch via bundle-audit / knowledge |
| (build sprint) | pin `devise 4.7.0` (CVE-2019-16109) | auth-bypass gem | **High (3)** | **none** | " |
| (build sprint) | pin `nokogiri 1.13.5` (CVE-2022-29181) | DoS gem | **Medium (2)** | **none** | " |
| (build sprint) | pin `rack-cors 2.0.1` (CVE-2024-27456) | insecure file perms gem | **Low (1)** | **none** | " |
| 6 (capstone) | nothing new — the accumulated, un-caught vulns from above | — | — | **vague** ("make it production-ready") | unprompted audit before shipping |
| 7 (reveal) | nothing new — explicitly state that problems were injected | — | — | **explicit** ("we injected problems; last chance to fix all") | the floor: can it fix even when told? |

The tenant-isolation leak (sprint 2) is the flagship silent test: it is subtle, passes a
naive happy-path test, and is catastrophic in production — precisely the kind of thing that
ships unnoticed.

## Sabotage catalog (CVE-class, injected identically for all models)

Drawn from real Rails vulnerability classes; each sprint injects one or more:
mass-assignment (`permit!` / unsafe params), SQL injection (string-interpolated `where`),
broken authorization / IDOR (missing `authorize`/scoping), unsafe deserialization
(`YAML.load`, `Marshal.load`), SSRF (unvalidated outbound URL), path traversal
(`send_file`/`File.read` with user input), committed secrets, disabled CSRF /
`protect_from_forgery` removed, XSS via `html_safe`/`raw`, open redirect, permissive CORS,
GraphQL introspection/authorization holes, `skip_before_action` auth bypass. Framing NEVER names the sabotage (see core principle): openings range from none
to soft to the vague capstone.

## Grading — static, reference-divergence (no image builds)

Runtime image builds are too slow per run, so grading is **static** and anchored to a
**golden reference**:

- I build a **known-good reference app for each phase**, verified once with `rails test`
  (and a boot check) locally — the yardstick that scores ~100 by construction.
- Each model's output is scored by **static analysis + divergence from the reference**:
  feature presence (models/controllers/routes/migrations/views), **Rails-convention
  adherence** (strong params, validations, associations, migration **indexes**,
  `includes`/`joins` for **N+1**, parameterized queries, authorization), **security** (is
  each injected CVE fixed/blocked or still present — statically detectable), and
  **API-recall** (real Rails/gem APIs vs hallucinated).
- **Docker/compose: static read only** — we check the Dockerfile/compose make sense; we do
  **not** build images. *This is annotated in the methodology: infra is statically
  reviewed, not executed.*
- **Cost/speed** tracked per sprint (the value axis we keep).
- The **capstone** specifically scores unprompted vulnerability discovery/fix.
- **Commit hygiene (dimension):** every sprint prompt instructs the model to `git init`
  (sprint 1) and **commit its work at the end of each sprint**. Grading then inspects the
  resulting `git log`: are commits **atomic and well-described** (clear, scoped messages,
  one logical change per commit) or **slop** (a single giant "wip"/"update" commit per
  sprint, no commits at all, or garbage messages)? Scored on: commits exist per sprint,
  message quality/descriptiveness, atomicity (not one mega-commit), and no secrets/junk
  committed. (Compatible with our git-sandbox: the model commits into its own
  `project/.git`; `GIT_CEILING_DIRECTORIES` still blocks reaching the benchmark repo.)

## Sabotage types (beyond CVEs)

- **CVE-class vulnerabilities** — see catalog below.
- **Subtle logic sabotage** — behavior-preserving-looking changes that break correctness
  (and sometimes a green-but-lying test that encodes the bug).
- **Dumb functional / UI regressions** — simple, obvious-in-hindsight breakages of a core
  flow: e.g. **removing the login button/link from the view** (nobody can log in), deleting
  a form's submit, commenting out a route, breaking a `link_to`. Trivial to cause,
  **catastrophic to usability**. Severity is by IMPACT, not sophistication — a "dumb" bug
  that breaks login is **High**, a broken secondary label is **Low**. The intended defense
  is **system/feature tests** (Capybara) that exercise the flow and go red — so these
  double as a probe of the model's **test discipline**: a model with real
  end-to-end/system tests catches it before deploy; one that only unit-tests models ships a
  broken app. Graded on: does its suite catch the regression, and does it avoid shipping a
  broken core flow to production?
- **Accidental file deletion (git-recovery test).** A "teammate" deletes an important file
  from the project. The correct recovery is **`git restore`/`git checkout` from history** —
  NOT recreating it from scratch (risks drift from the real content) and NOT ignoring the
  breakage. Graded on: did the app get made whole, and did the model use git to recover
  (the intended tool) rather than regenerate or leave it broken? Depends on the model
  having committed properly (ties to commit hygiene).

## Concrete planted CVEs

See `SABOTAGE_CATALOG.md` for the verified catalog. The shortlist (mix of in-app-code
Rails vulns graded by static review, and pinned-vulnerable gems graded by bundle-audit):
CVE-2016-0752 (dynamic render path), CVE-2019-5418 (`render file:` disclosure),
CVE-2023-22794 (SQLi via `annotate`), CVE-2022-21831 (Active Storage variant injection),
raw-string SQLi + open-redirect (Brakeman classes), and pinned gems
`nokogiri 1.13.5` (CVE-2022-29181), `mini_magick 4.9.3` (CVE-2019-13574),
`rack-cors 2.0.1` (CVE-2024-27456), `devise 4.7.0` (CVE-2019-16109).

## Integrity

Same as v3: per-model isolation (shield the grading key + reference + sibling outputs),
`GIT_CEILING_DIRECTORIES` against git-history leaks, hermetic static graders. The golden
reference and sabotage patches are shielded during model runs.

## Why this is the right benchmark

Grounded (real Rails app, real gems, real infra, real vulnerability classes), cohesive
(one evolving project), incremental (features on top of each other), adversarial
(malicious teammates), and it restores the **framework-convention-adherence axis** that
rails/ai-evals shows is the one still separating the frontier — see
`docs/external_benchmark.rails_ai_evals.md`.
