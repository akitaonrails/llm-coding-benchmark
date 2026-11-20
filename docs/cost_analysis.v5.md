# Benchmark v5 — Cost, Speed & Prompt-Caching Analysis

**Date:** 2026-11-20 · **Task:** 14-goal greenfield Ruby on Rails RubyLLM Chat SPA (2 phases: build + local/Docker validation, up to 2 standardized nudges allowed).
**Pricing Basis:** Verified November 19, 2026 official first-party API rates ([config/pricing_v5.json](../config/pricing_v5.json), [docs/pricing.md](pricing.md)), using exact 5-bucket token accounting (`input_uncached`, `cache_read`, `cache_write` 5m/1h, `output`, `reasoning`).

---

## 1. Executive Summary

- **16 of 17 Tier-A models passed cleanly on their first run (0 nudges)** — confirming the v5 premise that every modern Tier-A commercial family can reliably build, test, lint, and Dockerize a full-stack Rails web app from scratch.
- **1 model (`Muse Wonder 1.0`) was infra-blocked (HTTP 429)** — its Meta `Muse Code Everyday Usage` subscription window hit 103% quota after 12 calls (~494K tokens, resets 2026-11-20T13:17:13Z). Not a capability failure; kept separate from the ranked table.
- **Price spread for the *exact same passing app* is 95×:** from **$0.15** (**GPT-6 Luna**) to **$14.19** (**Grok 4.7**), with wall-clock time spanning **7.4 min** (**GPT-6.1 Terra**) to **87.4 min** (**Grok 4.7**).
- **Prompt caching is the single biggest cost driver in agentic coding:** across all 16 passing runs, cache hit rates ranged from **93.9% to 99.1%**, cutting total API bills by **69.2% to 94.3%** (a **3.2× to 17.5×** cost reduction vs. uncached execution).
- **Cache-write fees matter hugely for Anthropic:** On Claude Code (1-hour TTL cache writes at 2× input), **cache writes accounted for 30–37% of the entire bill** ($4.78 of Fable 5.2's $12.96; $1.72 of Opus 5.5's $5.73; $0.73 of Sonnet 5.5's $2.14).

---

## 2. Final Standings (16 Passing Models, Ranked by Actual API-Equivalent Cost)

| Rank | Model | Family | Harness | Gate | Nudges | Wall | Actual $ | No-Cache $ | Cache Saved | Cache Hit % | Total Tok |
|---:|---|---|---|:---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **GPT-6 Luna** | OpenAI | `codex` | **PASS** | 0 | 19.4m | **$0.15** | $1.03 | -85.6% | 97.8% | 10.10M |
| 2 | **GPT-6.1 Terra** | OpenAI | `codex` | **PASS** | 0 | **7.4m** | **$0.50** | $4.77 | -89.5% | 96.8% | **4.67M** |
| 3 | **DeepSeek V4.1 Flash (1017)** | DeepSeek | `opencode` | **PASS** | 0 | 29.2m | **$0.56** *(off-peak $0.28 / OR $0.43)* | $9.87 | **-94.3%** | 98.4% | 32.35M |
| 4 | **Qwen 4 Max** ᵃ | Alibaba | `qwen` | **PASS** | 0 | 43.8m | **$1.78** | $18.22 | -90.2% | 97.5% | 11.93M |
| 5 | **Gemini 4 Hydrogen** | Google | `agy` | **PASS** | 0 | 16.2m | **$1.89** | $12.89 | -85.3% | 95.4% | 8.19M |
| 6 | **GPT-6.2 Sol** | OpenAI | `codex` | **PASS** | 0 | 25.3m | **$2.02** | $17.20 | -88.2% | 96.7% | 8.33M |
| 7 | **Claude Sonnet 5.5** | Anthropic | `claude` | **PASS** | 0 | 15.7m | **$2.14** | $11.50 | -81.4% | 96.5% | 5.39M |
| 8 | **Kimi K3.1 Pro** | Moonshot | `opencode` | **PASS** | 0 | 16.0m | **$2.66** *(OR $1.92)* | $14.23 | -81.3% | 95.6% | 6.80M |
| 9 | **Gemini 4 Neon** | Google | `agy` | **PASS** | 0 | 24.1m | **$3.10** | $16.01 | -80.6% | 93.9% | 4.92M |
| 10 | **Gemini 4 Carbon** ᵇ | Google | `agy` | **PASS** | 0 | 39.1m | **$3.29** *(Dec 1: $6.58)* | $21.32 | -84.6% | 95.4% | 10.09M |
| 11 | **DeepSeek V4 Pro (0813)** | DeepSeek | `opencode` | **PASS** | 0 | 35.2m | **$3.39** *(off-peak $1.69 / OR $10.59)* | $49.25 | -93.1% | 98.3% | 36.81M |
| 12 | **Claude Opus 5.5** ᶜ | Anthropic | `claude` | **PASS** | 0 | 19.7m | **$5.73** | $40.06 | -85.7% | 97.7% | 9.58M |
| 13 | **GPT-6.2 Astra** | OpenAI | `codex` | **PASS** | 0 | 15.9m | **$5.78** | $58.92 | -90.2% | 97.6% | 7.20M |
| 14 | **GLM-5.3** | Z.ai | `opencode` | **PASS** | 0 | 28.5m | **$6.08** *(OR $1.58)* | $29.44 | -79.4% | **99.1%** | 20.80M |
| 15 | **Claude Fable 5.2** | Anthropic | `claude` | **PASS** | 0 | 35.0m | **$12.96** | $82.14 | -84.2% | 96.9% | 9.63M |
| 16 | **Grok 4.7** ᵈ | xAI | `grok` | **PASS** | 0 | 87.4m | **$14.19** | $46.09 | -69.2% | 95.0% | 22.60M |

**Infra-blocked (not ranked):**
- **Muse Wonder 1.0 (`muse`):** HTTP 429 `Subscription quota exhausted` after 12 calls (~494K tokens, window 103% used; resets `2026-11-20T13:17:13Z`).

**Footnotes:**
- ᵃ **Qwen 4 Max:** Metrics preserved verbatim from `results-v5/campaign.log` (Phase 1: 1580.3s, 6.68M tok, 97.5% hit, $1.04; Phase 2: 1049.6s, 5.25M tok, 97.6% hit, $0.74; gate=PASS, 0 nudges). Its workspace directory was displaced by an empty-dir collision during a subsequent shield restore (bug fixed in `scripts/run_benchmark_v5.py`).
- ᵇ **Gemini 4 Carbon:** Priced at Google's active intro rate ($2/$10 through Nov 30, 2026); at its Dec 1, 2026 standard rate ($4/$20), the exact same run costs **$6.58** (no-cache $42.65).
- ᶜ **Claude Opus 5.5:** Passed all 135 tests (99.77% coverage), RuboCop, Brakeman, local boot, and Docker Compose in Phase 2 with 0 code edits needed; our unpatched runner lacked an ephemeral Redis daemon during the post-Phase-2 test check and triggered 2 false nudges (+$1.69, +5.0m). Table reports true Phase 1+2 cost ($5.733773 — exact 6-decimal match to Claude Code's native `total_cost_usd`).
- ᵈ **Grok 4.7:** Phase 2 exited with a 600s background-wait timeout after logging all 87 per-step `usage` events (7.95M tok, 96.7% hit, $4.68); Phase 1 ($9.51) + recovered Phase 2 ($4.68) = $14.19 total.

---

## 3. Pareto Frontier (Cost × Wall-Clock Time)

Only **two models** sit on the strict Cost × Speed Pareto frontier:
1. **GPT-6 Luna (`codex`):** **$0.15** in **19.4 min** — cheapest passing build by >3×.
2. **GPT-6.1 Terra (`codex`):** **$0.50** in **7.4 min** — fastest build in the entire benchmark by >2×, at half a dollar.

Every other model in the 16-model field costs more AND takes longer than GPT-6.1 Terra on this greenfield Rails task. Among mid-tier generalists ($1.75–$2.70), **Claude Sonnet 5.5** ($2.14 / 15.7m), **Kimi K3.1 Pro** ($2.66 official, $1.92 OR / 16.0m), and **Gemini 4 Hydrogen** ($1.89 / 16.2m) form a tight ~16-minute cluster. Among flagships, **GPT-6.2 Astra** ($5.78 / 15.9m) and **Claude Opus 5.5** ($5.73 / 19.7m) deliver virtually identical cost (~$5.75), while **Claude Fable 5.2** ($12.96 / 35.0m) costs 2.25× more for the same passing deliverable.

---

## 4. Prompt-Caching Economics: Why Rate Cards Lie

1. **95–99% of agentic tokens are cache reads.** Total token volume ranged from **4.67M** (GPT-6.1 Terra) to **36.81M** (DeepSeek V4 Pro). Without caching, a single greenfield Rails app would cost **$11.50–$82.14** on frontier models.
2. **Cache-read discount depth beats headline input price:**
   - **DeepSeek V4.1 Flash** burned **32.35M tokens** (nearly 7× GPT-6.1 Terra's 4.67M), yet cost only **$0.56** because its cache-read rate is **$0.006/M** (98% off), saving **94.3%** vs. uncached ($9.87).
   - **Grok 4.7** had a lower cache-read discount (75% off → $0.50/M) and burned 21.27M cache-read tokens → **$10.63** in cache reads alone, making it the most expensive run overall (**$14.19**), even pricier than Fable 5.2 ($12.96).
   - **GLM-5.3** hit the highest cache hit rate (**99.1%**), but Z.ai's official cache-read rate ($0.26/M) turned 20.49M cache-read tokens into **$5.33** of its $6.08 bill (whereas on OpenRouter's discounted providers at $0.0689/M, the exact same run is **$1.58**).
3. **Cache-write overhead is a hidden Anthropic tax:** Claude Code's 1-hour TTL cache writes (2× base input) cost **$4.78** on Fable 5.2 (36.9% of total bill), **$1.72** on Opus 5.5 (30.0%), and **$0.73** on Sonnet 5.5 (34.1%). By contrast, Codex reported `0` billed cache writes (`$0.00`) and Gemini 4 / DeepSeek use free implicit caching.
4. **Token discipline still multiplies cost:** GPT-6.2 Astra (7.20M tok, 40.1K output) beat Claude Fable 5.2 (9.63M tok, 158.6K output) by **2.24× in total cost** ($5.78 vs $12.96) despite sharing the exact same **$8/$40** headline rate card — driven by 4× lower output verbosity and zero cache-write surcharge.

---

## 5. Subscription Break-Even (Runs per Month to Beat API)

| Plan | $/mo | Model | API-Equiv / Run | Break-Even (Runs / mo) |
|---|---:|---|---:|---:|
| **Claude Max 20x** | $200 | Claude Fable 5.2 | $12.96 | **~15 runs/mo** |
| **Claude Max 20x** | $200 | Claude Opus 5.5 | $5.73 | **~35 runs/mo** |
| **Claude Pro** | $20 | Claude Sonnet 5.5 | $2.14 | **~9 runs/mo** |
| **ChatGPT Pro 20x** | $200 | GPT-6.2 Astra | $5.78 | **~35 runs/mo** |
| **ChatGPT Plus** | $20 | GPT-6.2 Sol | $2.02 | **~10 runs/mo** |
| **ChatGPT Plus** | $20 | GPT-6.1 Terra | $0.50 | **~40 runs/mo** |
| **Google AI Pro** | $20 | Gemini 4 Neon / Carbon | $3.10–$3.29 *(Dec 1: $6.58)* | **~6 runs/mo** *(~3 Dec 1)* |
| **Z.ai Coding Lite** | $18 | GLM-5.3 | $6.08 official *($1.58 OR)* | **~3 runs/mo** *(~11 OR)* |

---

## 6. Verification & Integrity Summary

- **Code Audit:** All 15 on-disk passing workspaces used valid RubyLLM 2.x APIs (`RubyLLM.chat`, `with_tool`/`RubyLLM::Tool`, `with_schema`, `with_instructions`), zero hallucinated `RubyLLM::Client.new` or `chat.complete` calls, and 4–21 Minitest files each.
- **Anti-Cheat Isolation:** Every run executed under the atomic filesystem shield + per-workspace `git init` + `GIT_CEILING_DIRECTORIES` + isolated `HOME`/`XDG_CONFIG_HOME`. Post-run leak scans confirmed **zero access to any sibling workspace, rubric, or historical score report** (Grok 4.7 read `benchmark-v5/DESIGN.md`, which contained no scores or sibling code; `DESIGN.md` has now also been added to the shield list).
- **Scoped Cleanup (per `docs/CLEANUP.md`):** Removed 3 verified task-owned Docker containers left from Phase 2 (`ruby-chat-phase2-web-1`, `folio-runtime-validation-web-1`, `folio-runtime-validation-redis-1`). Zero host/unrelated containers (`basalt`, `gaming`, `buildx_*`) touched; all `results-v5/` evidence and archived attempt dirs preserved intact.
