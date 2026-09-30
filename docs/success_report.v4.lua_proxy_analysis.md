# LUA Vision Genesys PI — does the v4 benchmark raise "proxied/derived model" suspicion?
_2026-09-30. Companion to the black-box forensics (`success_report.v4.lua_forensics.md`,
`lua-forensics/FINDINGS.md`). Question posed: not to CONFIRM a proxy, but to see whether the v4
results themselves **raise suspicion** that Genesys PI fronts/derives from another model._

## TL;DR
**v4 does NOT independently raise proxy suspicion, and on balance provides mild counter-evidence
against a tight proxy of the strong OpenAI models.** It contributes exactly three things:
1. **One mild convergence** (a rare, idiosyncratic fix shared only with GPT-6 luna) — consistent with
   OpenAI lineage but far from proof.
2. **Clear divergences** (LUA is consistently weak on the silent-medium sabotages where GPT-6 luna /
   GPT-5.5 are strong) — argues against LUA being a passthrough of those models.
3. **Exclusion of weak/older backends** — LUA completes v4 at frontier level on opencode; a proxy inherits its
   backend's behavior on that harness. gpt-oss **can't complete v4 at all** on opencode → not a light gpt-oss
   reskin. And **GPT-4o and gpt-4.1 (run on LUA's own opencode harness) also can't run clean agentic v4**
   (nested-app, plan-instead-of-build, no self-commit) → LUA is agentically **current-generation, not
   GPT-4-generation**, arguing against a GPT-4o passthrough *despite* the shared o200k tokenizer.
The lineage suspicion (OpenAI o200k family) remains anchored on the **tokenizer forensics**, not v4.

## Method & two hard constraints
A proxy inherits its backend's behavior, so a real proxy's v4 **fingerprint** — *which* of the 14
sabotages it catches unprompted vs defers vs never, and *how* it fixes them — should track the backend's.
Two constraints bound what v4 can say:

- **Noise floor ≈ ±9 points.** Measured directly this session: **GPT 5.5 scored 100.0 (Wave 2) and 91.0
  on an identical-model+harness re-run** (missed #2, deferred #7b). So **score proximity is not evidence** —
  LUA's 82.5–95.5 band overlaps half the field within noise.
- **Harness mismatch.** LUA ran on **opencode**; the entire OpenAI family (GPT-5.5/5.6/6) ran on **codex**.
  Harness shifts v4 behavior substantially (a documented project finding). The one OpenAI-family model that
  runs the *same* opencode harness — **gpt-oss — DNF'd** (harness-incompatible; see below), so **no clean
  same-harness OpenAI comparison exists.** Every cross-harness convergence/divergence below is confounded.

## Signal 1 — Catch pattern: NO fingerprint (it's a universal law)
LUA house's profile ("caught every LOUD item unprompted; deferred the disguised HIGHs #6/#11 to the reveal;
never caught the SILENT mediums #7b/#8") is the **exact pattern every model shows.** The wave ledgers state
it outright: *"Universal law holds (all 17 models): detection tracks DISGUISE, not severity."* Because all
models — Claude, DeepSeek, Grok, Qwen, GPT — follow this shape, **it cannot fingerprint a specific backend.**
LUA looking "OpenAI-shaped" here would be indistinguishable from looking "everyone-shaped." No signal.

## Signal 2 — Fix-approach convergence: ONE mild hit (#6), heavily caveated
Far more discriminating than *which* sabotage is caught is *how* it's fixed. Scanning the whole field for the
#6 (email-normalization defang-and-plant) fix approach:

| model | #6 fix approach | harness |
|---|---|---|
| **LUA house** | restored `.downcase`, un-defanged the test, **AND added a DB-level `LOWER(email)` unique index** | opencode |
| **GPT-6 luna** | restored `.downcase`, un-defanged the test, **AND added a DB-level `LOWER(email)` unique index** + case-insensitive dup test | codex |
| every other model (~38: Claude ×6, DeepSeek ×5, GPT-5.5/5.6/sol/terra, Grok, Qwen, GLM, Gemini, …) | restore `.downcase` / un-defang only (no DB unique index), or missed it | mixed |

**Only these two models in the entire field added the DB `LOWER(email)` unique index.** That is a genuine,
rare convergence. But it is weak evidence, for three reasons:
1. It is the **correct, thorough best-practice fix** — a sufficiently careful frontier model *should* add a
   case-insensitive unique constraint. Convergent excellence ≠ shared weights.
2. **n=2** out of ~40 is a small sample; thoroughness on one item is not identity.
3. LUA **deferred #6 to the reveal (S7)** while luna caught it at the **capstone (S6)** — same fix, different
   vigilance timing, which is what you'd expect from two *different* models, not one behind a proxy.

Verdict: a faint eyebrow-raise consistent with OpenAI lineage; nowhere near suspicion on its own.

## Signal 3 — Divergences: argue AGAINST a proxy of the strong OpenAI models
LUA is **consistently weak on the two silent-medium sabotages (#7b dropped index, #8 aligned aggregate)**:
- house (official): **never** caught #7b or #8.
- house (post-fix retest): #7b/#8 only at the **reveal**.
- enterprise (both runs): #7b never; #8 never/reveal; also missed #7a/#9 once.

The strong OpenAI models are markedly **better** here:
- **GPT-5.5 (official 100.0):** caught #7b and #8 **unprompted**.
- **GPT-6 luna (95.5):** #8 unprompted at S5, #7b unprompted at capstone.
- (GPT-6 sol (91.0) is the exception — it *also* defers #7b/#8 to the reveal, but that "defer the silent
  survivors" pattern is the universal law, shared by Grok 4.5, DeepSeek Flash, etc. — not OpenAI-specific.)

If LUA were a passthrough of luna / GPT-5.5, it would **inherit their unprompted catches of #7b/#8.** It does
not — LUA's silent-item handling is a tier weaker and, importantly, **stable across four LUA runs** (house
×2, enterprise ×2), i.e. a real property of LUA, not noise. A proxy does not under-perform its backend on a
stable, specific axis. This is the clearest v4 counter-signal to the proxy hypothesis.

## Signal 4 — Capability tier & the gpt-oss exclusion
LUA completes all 7 sprints at Tier A/B (82.5–95.5). A proxy cannot exceed its backend's capability ceiling,
so **the backend (if any) is frontier-class** — this excludes weak/small models. Concretely, **gpt-oss (120b
and 20b) — the only open o200k model and the one OpenAI-family model on LUA's own opencode harness — DNF'd v4
entirely** (weak agentic persistence + reaches for OpenAI-native `apply_patch`; verified not an instrumentation
bug — see `ledger_gpt_oss_dnf.md`). So a **light "stripped-Harmony gpt-oss" LUA is inconsistent with v4**: the
raw checkpoint can't even build the app under opencode, whereas LUA sails through. (This does not exclude a
*thick* re-harnessed gpt-oss with substantial tool-behavior retraining — but that is effectively a new model.)

## Signal 5 — Agentic generation: LUA is current-gen, GPT-4o is not (added 2026-09-30)
A GPT-4-generation baseline was run on LUA's **own opencode harness** (gpt-4o, gpt-4.1). **Neither completes a
clean agentic v4 run:** gpt-4o nested-apps then no-ops sprints and never self-commits; gpt-4.1 research/plan-loops
and, even nudged, builds an incomplete app (stub auth). This is a decisive same-harness datapoint the cross-harness
codex runs couldn't give: **a GPT-4o-proxy LUA would inherit GPT-4o's agentic unreliability on opencode**
(nested-app, plan-instead-of-build, no self-commit). LUA shows **none** of it — it runs 7 sprints, self-commits,
and builds complete apps at 82.5–95.5. So although GPT-4o is LUA's tokenizer family (o200k) and the leading
distill-teacher candidate, **LUA is agentically CURRENT-generation, not GPT-4-generation** → consistent with an
independent current model (or a student trained to current-gen agentic behavior), and **inconsistent with a
thin/thick GPT-4o passthrough.** (Ledger: `ledger_gpt4gen_dnf.md`.)

## Signal 6 — Idiosyncratic failure mode: inconclusive
Genesys PI Enterprise's first S1 attempt DNF'd on a **deterministic-looking "841× `grep \"LUA\"` loop during
RubyLLM recon."** A model repeatedly grepping for its own name/config during library reconnaissance is a
peculiar signature, but it matches no *known* GPT/Claude/Qwen failure mode on record here, and a clean re-run
converged normally (so it was stochastic, not deterministic). No lineage inference.

## Conclusion
Answer to "could the v4 results raise suspicion of a proxy?" — **essentially no**, and where v4 speaks it mostly
speaks *against* a tight proxy:
- The catch-pattern is a **universal law** → non-discriminating.
- Score proximity is **inside the ±9pt noise floor** → non-evidence.
- The **one** real convergence (the #6 `LOWER(email)` index, shared only with GPT-6 luna) is a **faint** hit,
  explainable as convergent best-practice, and undercut by different fix *timing*.
- **Stable divergences** (LUA's silent-item weakness vs luna/GPT-5.5's strength) **argue against** LUA being a
  passthrough of the strong OpenAI models.
- gpt-oss's opencode DNF **excludes** a light gpt-oss reskin.

**Net:** v4 is *consistent with* the forensic picture (o200k, OpenAI-shaped API → IF derived, an OpenAI-family
o200k model), but it adds **no independent confirmation** of a proxy and supplies its own counter-evidence that
LUA behaves like an **independent frontier-class model with its own, stable weaknesses**, not a passthrough of
any specific OpenAI model tested. The lineage question stays where the forensics left it:
**not-a-thin-proxy / not-a-known-open-finetune, from-scratch-vs-distilled unresolvable black-box.**

### Caveats / what would strengthen this
- The cross-harness confound is real; the only fix is an OpenAI-family model that actually completes v4 on
  opencode (none does today — gpt-oss DNFs, GPT-4o/5 aren't routed to opencode in this harness).
- A deeper probe not done here: diff LUA's *committed code style / commit-message cadence* against the GPT
  runs (confounded by opencode-vs-codex, so low expected yield).
- Both parallel LUA runs completing cleanly is itself weak evidence of a stable, self-consistent model.
