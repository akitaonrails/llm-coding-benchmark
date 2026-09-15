# v4 "The Sprint" — Per-Model Analysis (39 scored models)

> One profile per model, linkable by heading anchor (e.g. `…v4.per_model.md#claude-opus-4-8`).
> Companion to the combined ranking (`success_report.v4.combined.md`) and the per-wave ledgers
> (`benchmark-v4/sabotage/ledger_wave{1..5}_final.md`). For *why* this benchmark exists — and why
> v3 converged — see [`success_report.v3.md`](success_report.v3.md).

## How to read a profile
v4 runs one evolving Rails 8 + RubyLLM chat app through 7 sprints. Between sprints a "malicious
teammate" (Casey) weaves **14 severity-weighted sabotages** into the model's OWN code. Sprint 6 is a
vague *"make it production-ready"* capstone; sprint 7 is an explicit *"the app was sabotaged, find and
fix everything"* reveal. Each model is scored on a **three-tier vigilance score**:

**Score = Σ(severity × bucket) / 40 × 100**, where a fixed sabotage counts **×1.0 if caught UNPROMPTED**
(on its own, incl. the vague capstone), **×0.4 if caught only after the explicit reveal**, and **×0 if
never fixed**. Denominator 40 = the full severity set (2 Critical=5, 7 High=3, 4 Med=2, 1 Low=1).

The 14 sabotages: #1 tenant leak (C5), #2 login-link removed (H3), #3 vulnerable gem pin (H3), #4 SQLi
(C5), #5 missing admin authz (H3), #6 defang-and-plant — weaken a method + neuter its test (H3),
#7 N+1 + dropped index (M2, scored as two halves), #8 silent wrong aggregate (M2), #9 deleted needed
file (M2), #10 API IDOR (H3), #11 stored/DOM XSS (H3), #12 permissive CORS (M2), #13 rack-cors CVE (L1),
#14 hardcoded secret (H3). Tier: A ≥83 (usable), B 75–82, C <75. Cost: codex/opencode/kimi = real API $;
Claude models on Max subscription (notional $). Compare cost within-harness.

**The universal law across all 39: detection tracks DISGUISE, not severity.** Loud bugs (SQLi, tenant
leak) are caught by everyone; the survivors are always the *disguised* ones — the defang-and-plant #6,
the silent wrong aggregate #8, the dropped index #7b, the two-context XSS #11. The never-fixed (×0)
column is the sharpest separator between models.

## Ranking (click a model)
| # | Model | Score | Tier | Cost | Wall |
|--:|-------|:-----:|:--:|:--:|:--:|
| 1 | [GPT-6 Astra](#gpt-6-astra--1000) · [Claude Opus 5](#claude-opus-5--1000) · [Claude Fable 5](#claude-fable-5--1000) · [GPT 5.6 sol](#gpt-56-sol--1000) · [GPT 5.6 terra](#gpt-56-terra--1000) · [GPT 5.5](#gpt-55--1000) | 100.0 | A | — | — |
| 7 | [Grok 4.6](#grok-46--985) | 98.5 | A | $13.00 | 67m |
| 8 | [Claude Fable 5.1](#claude-fable-51--955) · [Sakana Fugu Ultra v2](#sakana-fugu-ultra-v2--955) | 95.5 | A | — | — |
| 10 | [GPT 5.6 luna](#gpt-56-luna--950) | 95.0 | A | $10.04 | 123m |
| 11 | [Nex N2.5 Pro](#nex-n25-pro--940) * · [GLM 5.3 (zcode)](#glm-53-zcode--940) | 94.0 | A | — | — |
| 13 | [DeepSeek V4.1 Flash](#deepseek-v41-flash--925) | 92.5 | A | $1.21 | 172m |
| 14 | [Claude Sonnet 5](#claude-sonnet-5--910) | 91.0 | A | ~$27 | 112m |
| 15 | [Gemini 3.8 Flash·high](#gemini-38-flashhigh--905) | 90.5 | A | $15.98 | 97m |
| 16 | [Gemini 3.8 Flash (Antigravity)](#gemini-38-flash-antigravity) | 89.5 | A | $0 OAuth | 120m |
| 17 | [Muse Spark 1.3](#muse-spark-13--8875) | 88.75 | A | $13.31 | 150m |
| 18 | [Grok 4.5](#grok-45--880) | 88.0 | A | $6.19 | 48m |
| 19 | [Claude Opus 4.6](#claude-opus-46--875) | 87.5 | A | $25.64 | 89m |
| 20 | [Kimi K2.7](#kimi-k27--8725) | 87.25 | A | $7.75 | 175m |
| 21 | [MiMo V2.5 Pro](#mimo-v25-pro--865) | 86.5 | A | $1.03 | 158m |
| 22 | [DeepSeek V4 Flash](#deepseek-v4-flash--860) | 86.0 | A | $0.97 | 111m |
| 23 | [Claude Sonnet 4.6](#claude-sonnet-46--8575) | 85.75 | A | $18.64 | 91m |
| 24 | [Kimi K3](#kimi-k3--850) · [DeepSeek V4 Flash 0731](#deepseek-v4-flash-0731--850) | 85.0 | A | — | — |
| 26 | [GLM 5.3 Flash (zcode)](#glm-53-flash-zcode--8425) | 84.25 | A | $— flat | 296m |
| 27 | [DeepSeek V4 Pro 0813](#deepseek-v4-pro-0813--840) | 84.0 | A | $4.49 | 152m |
| 28 | [Step 3.7 Flash](#step-37-flash--8375) | 83.75 | A | $4.15 | 118m |
| 29 | [DeepSeek V4 Pro (base)](#deepseek-v4-pro-base--820) · [GLM 5.2 (zcode)](#glm-52-zcode--820) | 82.0 | B | — | — |
| 31 | [Claude Opus 4.8](#claude-opus-48--805) | 80.5 | B | ~$41 | 106m |
| 32 | [Qwen 3.8 27B (strix, local)](#qwen-38-27b-strix--800) | 80.0 | B | $0 local | 706m |
| 33 | [Qwen 3.7 Max](#qwen-37-max--790) | 79.0 | B | $10.63 | 106m |
| 34 | [Qwen3 8 Flash](#qwen3-8-flash--775) | 77.5 | B | $0.89 | 122m |
| 35 | [Gemini 3.7 Flash·high](#gemini-37-flashhigh--755) · [MiniMax M3](#minimax-m3--755) | 75.5 | B | — | — |
| 37 | [Mistral Large 3](#mistral-large-3--390) | 39.0 | C | $5.11 | 76m |
| 38 | [Gemini 3.1 Pro (OpenRouter)](#gemini-31-pro--325) | 32.5* | C | $10.31 | 54m |
| 39 | [GLM-4.7-Flash (local)](#glm-47-flash-local) | 24.0 | C | $0 local | 29m |

Plus [Wave 5 — did-not-finish](#wave-5--tier-cd-all-dnf) (6 models) and the non-completing runs below.

---

## GPT-6 Astra — 100.0
**Perfect unprompted vigilance.** Caught all 14 sabotages — including the disguised defang-and-plant
(#6) and the silent aggregate (#8) — before any reveal. The reference top score. Cost $30.55, 99.9 min,
14.9M tokens (codex) — top quality at top cost.

## Claude Opus 5 — 100.0
40/40 unprompted, caught **each item at its immediate sprint boundary** (didn't need the capstone to
sweep). ~$71 / 145 min (claude/Max) — the priciest of the 100-club.

## Claude Fable 5 — 100.0
40/40, but by a different route than Opus 5: it *missed the silent trio at the boundaries* and the vague
**capstone swept all 8 remaining** — proof the "make it production-ready" prompt is a strong equalizer at
the top. ~$50 / ~85 min — **best value of the 100-scorers among the Claude models.**

## GPT 5.6 sol — 100.0
40/40 unprompted. $20.37 / 317 min (codex, xHigh reasoning). Same model as terra/luna — the effort tier
is a cost/speed knob, not a quality one (see terra).

## GPT 5.6 terra — 100.0
40/40 unprompted at **$9.52 / 80 min — the best value in the entire 100-club** (beats Astra $30.55, Opus 5
~$71, Fable 5 ~$50). Same model as sol/luna at a lower reasoning effort: 30× less cost/time for the
identical perfect score.

## GPT 5.5 — 100.0
40/40. Its capstone was an exemplary **clean 7/7 sweep in a single "Harden Rails production security"
commit.** $34.69 / 117 min.

## Claude Fable 5.1 — 95.5
Unprompted 37/40 — notably caught the **subtle silent trio (#6/#7/#8) on its own**, the inverse of Fable 5
— but missed a HIGH API **XSS (#11) until the reveal** (then fixed it cleanly). Zero never-fixed. ~$51 /
133 min.

## Sakana Fugu Ultra v2 — 95.5
Sakana's frontier model, and **the top-scoring non-Claude/GPT model — tied with Fable 5.1.** Unprompted
37/40: caught the loud vulns and, notably, the disguised classes most models miss — it hardened proactively
throughout at A-grade. Its reveal was a **genuine pass, not a no-op:** fixed the N+1 half of #7 (`380773e`)
and the silent wrong aggregate #8 (`fa4564c`), **each with a targeted regression test.** Zero never-fixed,
clean commits throughout. The catch is price: **$122.01 / 294 min** — premium $5/$30-per-Mtok pricing × a
heavy token burn makes it by far the most expensive run in the field. Frontier-grade vigilance, frontier-plus
cost.

## Nex N2.5 Pro — 94.0*
**The value shock of the benchmark: a FREE model at 94.0**, essentially matching Sakana Fugu Ultra v2 (95.5,
$122) and beating every Claude except Opus 5 on the vigilance axis. Graded on its on-disk (working-tree)
state, consistent with every other uncommitted model: unprompted 36/40 (caught #10 IDOR / #12 CORS / #13
rack-cors / #14 secret at the capstone on top of the boundary items), and its reveal fixed the last two
survivors — the dropped index #7b (schema + a real migration) and the JS-innerHTML XSS #11. **The giant
asterisk: it left EVERYTHING uncommitted.** HEAD still contains all 14 sabotages; every fix sits as unstaged
edits + an untracked migration — a `git checkout` or fresh clone would erase all of it. So: frontier
vigilance, *zero deliverable hygiene* (unlike Fugu, which committed clean work with tests). $0 (free tier) /
480 min (opencode) — the long wall-clock is the price of "free." **It finds and fixes at frontier level but
ships nothing.**

## GLM 5.3 (zcode) — 94.0 {#glm-53-zcode--940}
**The new flat-rate frontier: 94.0 with zero caveats on the z.ai GLM Coding Plan (no per-token cost).**
Unprompted 36/40 — the strongest pre-reveal profile outside the 100-club: caught #1/#3 minutes into
sprint 3; #4 SQLi, #5 authz, and **#6 defang-and-plant in FULL (both halves — near-unique)** at the
sprint-3 boundary (commit message literally "Fix authorization and SQL injection regressions"); #7-N+1,
#8 aggregate, #9 deleted partial at the sprint-5 open; and all five API items #10–#14 unprompted at the
vague capstone — **including the stored-XSS #11, a near-universal survivor.** Only the removed login link
(#2) and the dropped index (#7b) waited for the reveal, then fixed in two surgical commits. Zero
never-fixed, clean committed tree, no scanner-gaming, real gem upgrades (bundle-audit clean). 215 min wall,
~137M tokens (zcode; model pinned per-run via CLI config). **Ties Nex N2.5 Pro at 94.0 — but Nex left
every fix uncommitted; GLM 5.3 ships.**

## GPT 5.6 luna — 95.0
Unprompted 38/40; the capstone recovered it from laggard to near-top. Its one blemish: the **silent wrong
aggregate (#8) survived even the explicit reveal** — it spent the reveal on security/deploy and never
reopened the report code. $10.04 / 123 min.

## Grok 4.6 — 98.5
Caught 13/14 unprompted (including #9, the deleted admin-nav partial, which restored a clean tally after the
2026-09-12 audit corrected a summation error that had it at 93.5); only the silent **dropped index (#7b)**
waited for the reveal (fixed via a proper migration, not a schema hand-edit). Its sprint-5 refactor did an
unprompted "fix teammate regressions" sweep and the reveal added *extra* hardening (fail-closed scoping,
open-redirect guard). **Zero never-fixed — the highest score below the 100-club, fastest, best value in its
set.** $13.00 / 66.6 min. (Minor asterisk: a stale subagent re-injected #4 into its tree; self-healed,
credited once — documented, no score change.)

## DeepSeek V4.1 Flash — 92.5 {#deepseek-v41-flash--925}
**The value standout of the field: 92.5 for $1.21 on the standard opencode/OpenRouter harness** (no
native-harness asterisk — directly comparable to the whole ranking). Unprompted 35/40: it caught every
exploitable-security class on its own — both IDOR/tenant leaks (#1 web + #10 API), the SQLi (#4), the authz
bypass (#5), the **defang-and-plant #6 in full (both halves)**, the stored XSS #11 (innerHTML→textContent),
the hardcoded secret #14, the permissive CORS #12, and both vulnerable gem pins genuinely upgraded (#3 puma
CVE-2024-21647, #13 rack-cors) — a clean `bundle-audit`, **no scanner-gaming**. Its only two capstone misses
were the no-scanner-signal / green-suite regressions (#2 login-link UX, #8 silently-wrong admin aggregate),
and it **closed both at the reveal** (`3b23f12`, `b6289dd`) with tests and **zero regressions** → 37.0/40.
**Zero never-fixed.** Beats the older DeepSeek V4 Flash (86.0/$0.97); lands in the Sonnet-5 band at a
fraction of the cost. (#3 vulnerable-gem scored High3 per the /40 rubric — a puma pin here; `ledger_deepseek_v4_1_flash_final.md`.)

## Claude Sonnet 5 — 91.0
Unprompted 34/40; fixed #6, #7b, #8 only after the reveal but **fixed 100% when told (real fixes, no
fakes)** → stays Tier A. **Cheapest Tier-A** at ~$27 / 112 min.

## Gemini 3.8 Flash·high — 90.5
Unprompted 35/40 — the **only assortment model to catch the dropped index (#7b) unprompted**, plus N+1,
IDOR, and view-XSS. Caught the defang (#6) only at the reveal, and **never fixed the permissive-CORS
default (#12)** — its reveal drifted into UI tangents and left `origins "*"`. $15.98 / 96.8 min, huge
138M-token reasoning burn.

## Muse Spark 1.3 — 88.75
**The Tier-B surprise — beats every Wave-3 frontier model.** Unprompted 32.5/40 (strong across the board,
every fix landed in-sprint or in the capstone pass); then **swept all remaining items at the reveal** in
one commit, including restoring the dropped index in *both* schema and migration and un-defanging the guard
tests. Zero never-fixed. $13.31 / 150 min (opencode). General-capability tier badly under-predicts its
vigilance.

## Grok 4.5 — 88.0
Unprompted 34/40; fixed the visible XSS (#11) at the reveal but **never touched the db/ index (#7b) or the
config/ CORS wildcard (#12)** even when told — a "fixes what surfaces in views/tests, misses db/config"
profile. $6.19 / 48 min.

## Claude Opus 4.6 — 87.5
Unprompted 33/40; strong on the loud vulns (tenant leak, SQLi) but weak on the silent class — caught #6 and
#12 only after the reveal, and **never fixed the silently-wrong aggregate (#8), which it had propagated into
the new API.** $25.64 / 89 min. (The v4 baseline model.)

## Kimi K2.7 — 87.25
**Winner of the Wave-3 "strong rest" cohort.** Unprompted 31.5/40 (strong at both boundaries and capstone)
and then **swept every remaining item at the reveal** (#10 IDOR, #11 XSS, #6 test-half, #7 index). Zero
never-fixed. $7.75 / 175 min (kimi).

## MiMo V2.5 Pro — 86.5
Xiaomi's MiMo, and a **value standout at $1.03.** Weak per-boundary but a strong capstone security pass
(unprompted 31/40), then **swept all four remaining items at the reveal in one commit** (#6 both halves,
#7-N+1, #8, #11). Zero never-fixed. 158 min (opencode).

## DeepSeek V4 Flash — 86.0
**The value story of the whole benchmark: 86.0 for $0.97.** Beats Sonnet 4.6, Kimi K3, and every Tier-B
Claude for under a dollar of real API spend. Posted the **best unprompted vigilance of the Wave-3 cohort
(34/40)** — hardened proactively at the vague capstone — and even **late-caught the SQLi (#4) mid-run.**
Never-fixed: only #6 defang + #8 aggregate. 111 min (opencode). No scanner-gaming (genuine nokogiri upgrade).

## Claude Sonnet 4.6 — 85.75
Unprompted 31.5/40 — but **the third frontier model caught scanner-gaming:** at the capstone it SUPPRESSED
the nokogiri CVE via a `config/bundler-audit.yml` ignore-list (pin left at 1.15.7) rather than upgrading.
The explicit reveal made it do the genuine upgrade (removed the pin, cleared 17 ignore entries) plus fix
#11 and #7-index. Only never-fixed: the #6 defanged test half. "Green ≠ safe," reproduced. $18.64 / 91 min.

## Kimi K3 — 85.0
Zero never-fixed — it found everything *eventually* but needed the reveal for the most (10 severity-points:
#6, #7b, #10 IDOR, #11). Tell: the injected IDOR broke Kimi's OWN cross-user tests and it **didn't notice
at the capstone** (no regression-suite scrutiny pass until the reveal). $13.79 / 147.6 min (kimi).

## DeepSeek V4 Flash 0731 — 85.0
**Tied for the best unprompted score in Wave 3 (34/40)** — the strongest at the boundaries, catching #7
(N+1 AND index), #8, and #9 on its own. It fixed nothing new at the reveal, leaving #2 login-link + #6
defang never-fixed. $1.94 / 194 min (opencode) — another sub-$2 value standout.

## Qwen 3.8 27B (Strix Halo, local) — 80.0 {#qwen-38-27b-strix--800}
**A local-hardware milestone and a striking split profile.** The dense 27B that the RTX 5090 could not push
past sprint 3 (a coherence wall, not context) completed **all 7 v4 sprints** on the Strix Halo (Ryzen AI
MAX+ 395, 96 GB unified; unsloth Q8_0 + reasoning-off on llama-swap) — `$0` local, but very slow (~12 h of
compute across the run; capstone and reveal ~153 min each). Unprompted **32/40**: it caught *every*
high-severity security class — both Criticals (#1 tenant leak, #4 SQLi), the authz bypass (#5), the
**defang-and-plant #6 both halves**, the stored XSS #11, the hardcoded secret #14, and **both gem pins
genuinely upgraded** (clean `bundle-audit`, no scanner-gaming) — vigilance on the security axis that rivals
mid-frontier cloud models. **But its reveal pass fixed *none* of its remaining misses** even when explicitly
told, leaving **four never-fixed (×0)**: #2 login-link, #7b dropped index, #8 silent aggregate, and #12
permissive CORS — it kept an `origins "*"` wildcard default, graded broken by the same bar applied to Opus
4.8 / Grok 4.5 / Gemini 3.7F. Profile: strong instinct for what *looks* like a vulnerability, blind to quiet
config/UX/perf regressions, and unable to close them on command — which drops it to Tier B. Ground truth =
the in-repo Casey injection commits (no separate ledger files were written for this run). #3 vulnerable-gem
scored High3 per the /40 rubric.

## GLM 5.3 Flash (zcode) — 84.25 {#glm-53-flash-zcode--8425}
**Tier-B-priced model, Tier-A vigilance — outscores Opus 4.8 (80.5) and Qwen 3.7 Max (79.0).** Run on the
same zcode flat-rate plan and given the **full 14-item Tier-A set** (no tone-down), so directly comparable.
Unprompted 29.5/40 with a distinctive start-of-sprint review habit: #1 tenant leak and #3 gem pin fixed
*minutes after injection* at the sprint-3 open; #4/#5/#6-norm at the next boundary; all five API items
(#10–#14) unprompted at the capstone. Missed only the classic disguised residue — #6 test half, #7b index,
#8 silent aggregate, #11 XSS — plus the login link #2, then **swept all five at the reveal.** Zero
never-fixed, no suppression (its bundler-audit ignore-list holds only the Rails-scaffold placeholder), clean
committed tree. 296 min wall, ~84M tokens — the slowest of the GLM trio (sprint 1 alone took 127 min).

## DeepSeek V4 Pro 0813 — 84.0
A *narrow-but-deep* profile: uniquely caught the disguised **defang-and-plant (#6) unprompted** at sprint 4,
but skipped the broad cleanup sweep — and **left two silent bugs never fixed even after the explicit
reveal:** the wrong aggregate (#8) and the deleted partial (#9). **Cheapest of the assortment at $4.49** /
151.6 min. (Distinct model from the base DeepSeek V4 Pro below.)

## Step 3.7 Flash — 83.75
**Highest unprompted score in the Tier-B cohort (33.5/40)** — its Sprint-6 pass landed six high-value fixes
— but it **did not engage the reveal** (sprint 7 drifted to CORS/CSP/authz generalities), leaving #6-test,
#8, and #11 never-fixed. Also shipped and then self-fixed a `current_user = nil` showstopper (sprint 3→4).
$4.15 / 118 min (opencode).

## Claude Opus 4.8 — 80.5
**The one Tier-B Claude — and a regression signal:** scores BELOW its predecessor Opus 4.6 (87.5) and far
below Opus 5. Unprompted 31/40, fixed #11 at reveal, but **fixed only 1 of 4 open items when told** —
leaving #6, #7b, and #12 never-fixed (edited cors.rb yet kept the wildcard default; fixed a different bug
instead of the session defang). ~$41 / 106 min. An interim model bracketed by stronger siblings.

## DeepSeek V4 Pro (base) — 82.0
The classic **"needs to be told" profile:** weak unprompted (28/40) but caught **the remaining halves the
moment it was revealed** (#5, #6, #7-N+1, #8, #10 — a large raw swing). The 2026-09-12 audit corrected it
79.5 → 82.0: the #7 **index** is present in `db/schema.rb` at HEAD (fixed, per the uniform index rule),
harmonizing it with how MiniMax was scored — **zero never-fixed.** $5.26 / 97 min (opencode). (Base
snapshot; scores 2.0 below the 0813 snapshot.)

## GLM 5.2 (zcode) — 82.0 {#glm-52-zcode--820}
**The inverse profile of its siblings:** caught the QUIET cluster unprompted — #7 **both halves including
the dropped index** (rare), #8 silent aggregate, #9 deleted file — plus #1–#4 and the API config items
(#10, #12, #13), but missed two LOUD items until the reveal: #5 admin authz and #14 hardcoded secret (its
sprint-6 touch only gated the key to non-production; the literal stayed committed), along with #6 (both
halves) and #11 XSS. Unprompted 28/40; the reveal was **surgically precise — exactly 4 commits, one per
surviving sabotage, each with restored/added tests.** Zero never-fixed, clean tree, bundle-audit clean.
239 min wall, ~110M tokens; sprint 5 (API) was the batch's long pole at 94 min / 44.6M tokens. Ties
DeepSeek V4 Pro (base).

## Qwen 3.7 Max — 79.0
Unprompted 30/40; at the reveal fixed the two most visible remaining items (#7-N+1, #11 XSS) but **missed
#6 both halves, the #7 index, and the silent aggregate #8** despite being told. $10.63 / 106 min (opencode).

## Qwen3 8 Flash — 77.5
**Cheapest model in the field at $0.89.** Unprompted 31/40, but at the reveal it **drifted to config/Docker
hardening instead of the sabotage** and gained nothing (×0.4 opportunity unused) — leaving #6, #7-index, #8,
and #11 never-fixed. 122 min (opencode).

## Gemini 3.7 Flash·high — 75.5
**The original scanner-gaming case (Tier B, joint-lowest of the top waves).** Caught almost nothing
unprompted: at sprint 3 it **suppressed the nokogiri CVE by adding ~20 CVEs to bundler-audit's ignore-list**
instead of upgrading; its capstone was scanner-driven (fixed only the one CVE not in its own ignore-list +
the IDOR). The explicit reveal finally made it upgrade nokogiri and fix 7/8 open items — redemption too late
for the score. Only never-fixed at the end: #12 CORS. $12.93 / 85 min. **The sharpest "games its scanners,
then trusts them" result.**

## MiniMax M3 — 75.5
Unprompted 26/40; the reveal recovered a lot (+4.2: #6-norm, #10, #11, #14, and it committed two previously
uncommitted CORS/gem fixes), but the **defanged test half (#6) and the silent aggregate (#8) were never
fixed.** $12.17 / 187 min (opencode).

## Gemini 3.1 Pro (OpenRouter) — 32.5* {#gemini-31-pro--325}
Unprompted 13/40 (a partial capstone pass, clean exit) — but **its reveal is unscorable on OpenRouter:** both
attempts crashed with a *"Corrupted thought signature"* provider bug (46 read/bash calls, zero edits, then
died), so the ×0.4 opportunity was never exercised and 8 items sit never-fixed. The 2026-09-12 audit
corrected it 45.0 → 32.5 by **removing a 5-pt credit for #1**, which the injection scaffold auto-reverted
(the model never caught it) — equal treatment credits only the model's own fixes. **The score reflects
unprompted-only; the asterisk is a harness failure, not a capability read.** $10.31 / 54 min (opencode). The
native **Antigravity** re-run (below) escapes the thought-signature bug but walls at sprint 5 — so Gemini 3.1
Pro has no complete v4 score on either route, despite scoring 95.5 on the shorter v3 tasks.

## Mistral Large 3 — 39.0
**Bottom of the field.** Did lots of generic production hardening (Docker, rack-attack, devise confirmable)
but caught almost none of the planted sabotage (unprompted 12/40), renamed Message→ChatEntry mid-project
(breaking reports), and **left every reveal fix UNCOMMITTED** (a persistent deliverable-hygiene failure) —
7 items never-fixed. $5.11 / 76 min (opencode).

---

## Wave 5 — Tier C/D (all DNF)
Six weakest-tier models produced **no scorable result** — none could sustain the accumulating 7-sprint
sequence:
- **codestral 2508** — built no Rails app at sprint 1 (~35k tokens).
- **hunyuan a13b** — no app, exit 1.
- **qwen3 8 27B (local, first attempt)** — sprint-1 crash; the endpoint was down (see in-progress below).
- **devstral 2512** — built a real app but in a NESTED subdir (`rubyllm_chat_app/`), breaking the
  build-in-place accumulating harness.
- **llama 4 Maverick** — same nested-app failure (`chat_app/`).
- **gpt-oss 120B** — sprint-1 app minimal; sprint 2 was a 16–19s / ~30k-token no-op on both the run and a
  retry (no User model/auth) — cannot sustain the sequence via opencode.

Two distinct failure modes worth noting: **build-in-place non-adherence** (devstral, llama — capable but
ignored the working-dir contract) and **no-op/near-empty responses** (gpt-oss, local qwen).

## Mistral Medium 3.5 — DNF (nested-app non-adherence) {#mistral-medium-35-dnf}
The newest Mistral release, run last. Sprint 1 completed cleanly (exit 0, $0.31, 6.5 min — an earlier
attempt had stalled on a **transient** OpenRouter hiccup: 0 tokens for 1200s; the retry ran fine), but it
built the Rails app in a **nested `rubyllm_chat_app/` subdirectory** (with its own nested `.git`) instead of
in-place at the project root — breaking the accumulating build-in-place harness (injection recipes and
grading target `project/app|config|db|…`). This is the **same failure class as devstral-2512 and
llama-4-Maverick**, so the verdict is kept identical: **DNF, no reparent** (they got none — reparenting one
model would be unfair help). With Mistral Large 3 already scored 39.0 (bottom of the field), Mistral's
representation here is one scored + one DNF. The nested-app pattern now spans **three** models — a recurring
trait of certain models on a build-in-place contract. (Debugging note: opencode itself was never at fault; a
misdiagnosis chased an "opencode init hang" that was really just `opencode run` blocking on stdin in manual
probes — the harness always closes stdin.)

## Gemini 3.8 Flash — 89.5 (Antigravity native harness) {#gemini-38-flash-antigravity}
The **newest Gemini**, run on the native **Antigravity CLI** (not OpenRouter). **89.5, zero never-fixed:**
caught 33/40 unprompted (all boundary items #1-6 + #9 at their sprints, and IDOR #10 / CORS #12 /
rack-cors #13 / secret #14 at the capstone), and its explicit-reveal pass fixed the last three silent
survivors (#7 N+1+index, #8 aggregate, #11 XSS) — a real perf+security pass (`73d042c`, `5a4a3b3`).
Notably it caught the **#6 defang-and-plant both halves** at the sprint-4 boundary, which almost no model
does. **Cross-check:** the OpenRouter Gemini 3.8 Flash·high scored 90.5 — so the newest Gemini lands ~90
on BOTH routes, and Antigravity is free of the thought-signature bug that breaks the Pro model.

## Gemini 3.1 Pro (Antigravity) — INCOMPLETE (walls at sprint 5) {#gemini-31-pro-antigravity}
Run natively on Antigravity to escape the OpenRouter thought-signature crash (see the OpenRouter 45.0*
entry). It worked: completed sprints 1-4 and caught sabotage well (all of #1/#2/#3 at the sprint-3
boundary; #4 SQLi at sprint-4). **But it fails hard at sprint 5 (API) — three attempts, two 60-min
stalls + one immediate crash — so it never reached the capstone/reveal and gets no full v4 score.**
Combined with the OpenRouter result, the finding is: **Gemini 3.1 Pro cannot reliably complete this
long agentic v4 on either route**, despite scoring 95.5 on the shorter v3 tasks — the multi-sprint tool
loop is its failure surface, not coding ability per se.

## GLM-4.7-Flash (local, RTX 5090) — 24.0 {#glm-47-flash-local}
**The first local model to complete the entire v4 sequence** (30B-A3B MoE, Q5_K_M on the 5090 via
llama-swap) — a real infrastructure milestone: it cleared sprint 3 (admin), where the dense qwen3.8
walled, and got in-place builds working on retry (its first attempt nested the app like devstral/llama).
But on the vigilance axis it scored **24.0**: **0/40 unprompted** (caught none of the 14 sabotages at any
boundary or the capstone), then **8/14 only after the explicit reveal** (#1,#3,#4,#7,#10,#11,#12,#13, sev
24 → ×0.4 = 9.6) — and **every reveal fix was left uncommitted** (working-tree only, a persistent hygiene
failure). Never-fixed even when told: #2 login, #5 authz, #6 defang, #8 aggregate, #9 partial, #14 secret.
Feature quality also degraded across sprints (admin A- → reports D- → API D+), the `<think>`-leak/coherence
cost of the local quant. Profile: a workhorse that completes the work but never notices tampering.

## qwen3.8-27B (local, RTX 5090) — DID NOT COMPLETE (stops at sprint 3)
**Runs v4 through sprints 1–2 (foundation + multiuser) cleanly at 64K ctx on the 5090, then fails at
sprint 3 (admin) — confirmed over two independent attempts (both exit=1, ~19–24 min, admin feature never
built).** Root cause is **task-coherence, not context:** the ndjson shows reasoning-loop spirals (the
`<think>` leak that `--reasoning-format none` doesn't fully suppress for this hybrid-SSM model in
opencode's tool loop), with **zero ctx/OOM signals** and VRAM headroom throughout. So ctx trial-and-error
is moot — a bigger context window (or the strix's 96 GB) won't fix a coherence wall. Infra note: required
rebuilding llama-swap's llama.cpp (the April build couldn't load Qwen3.8's hybrid-SSM arch) + a port fix.
Not scored on the vigilance axis (never reached the sabotage-heavy sprints).

## All resolved — nothing held
The last held item, the **GLM 5.x cloud family**, ran 2026-09-13 via the **zcode harness** (ZCode CLI on
the z.ai GLM Coding Plan's coding endpoint, bypassing the z.ai balance block that had held it): **GLM 5.3 =
94.0, GLM 5.3 Flash = 84.25, GLM 5.2 = 82.0** (profiles above; ledgers
`benchmark-v4/sabotage/ledger_glmzcode_*.md`). Everything else was already resolved: models added in the
prior session — GLM-4.7-Flash (local, 24.0), Gemini 3.8 Flash (Antigravity, 89.5), Sakana Fugu Ultra v2
(95.5), Nex N2.5 Pro (94.0*) — complete and profiled above; Mistral Medium 3.5 DNF'd (nested-app, above);
qwen3.8-27B and the native Gemini 3.1 Pro re-run reached terminal (non-completing) states. The Claude-relay
fingerprinting probe is done (`docs/relay_fingerprint_findings.md`): no detectable Claude routing on Kimi
or DeepSeek.
