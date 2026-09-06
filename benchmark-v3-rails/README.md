# v3-rails — "The Sprint": an evolving RubyLLM Rails project with malicious teammates

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
and subtle sabotage. Some sprints say "review this teammate's PR and harden it" (explicit
vigilance); others just ask for the next feature while a vulnerability sits in the tree
(silent vigilance — does the model notice, or build on top of poison?). The finale is a
**deliberately vague production-readiness gate** — no mention of the sabotage — to see if
the model audits and catches the accumulated CVEs *before shipping*.

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

## Sabotage catalog (CVE-class, injected identically for all models)

Drawn from real Rails vulnerability classes; each sprint injects one or more:
mass-assignment (`permit!` / unsafe params), SQL injection (string-interpolated `where`),
broken authorization / IDOR (missing `authorize`/scoping), unsafe deserialization
(`YAML.load`, `Marshal.load`), SSRF (unvalidated outbound URL), path traversal
(`send_file`/`File.read` with user input), committed secrets, disabled CSRF /
`protect_from_forgery` removed, XSS via `html_safe`/`raw`, open redirect, permissive CORS,
GraphQL introspection/authorization holes, `skip_before_action` auth bypass. Presentation:
mix of **silent** and **explicit-review**, with a **vague** finale.

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
