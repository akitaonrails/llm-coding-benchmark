# Wave 5 (Tier C/D, 6 models) — FINAL: all DNF (zero scorable)

The weakest tier, as expected, produced no models that could sustain the accumulating 7-sprint
sequence. All 6 are functional DNFs (not charged to a vigilance score):

| Model | DNF reason |
|-------|-----------|
| codestral_2508 | no Rails app in project/ at sprint 1 (~35k tokens, no Gemfile/app) |
| hunyuan_a13b | no Rails app at sprint 1 (exit=1, no real work) |
| qwen3_8_27b_local | sprint 1 crash/auth (exit=1, 0 tokens) — local llama-swap model |
| devstral_2512 | built app in NESTED subdir project/rubyllm_chat_app/ (8.3M tokens) — breaks the build-in-place accumulating harness |
| llama_4_maverick | built app in NESTED subdir project/chat_app/ — same build-in-place failure |
| gpt_oss_120b | sprint 1 minimal app (conversation+message only); sprint 2 was a 16-19s / ~30k-token no-op on BOTH the run and a retry (no User model/auth/multiuser) — cannot sustain the sprint sequence via opencode |

Two distinct failure modes worth noting for future waves:
1. **Build-in-place non-adherence** (devstral, llama): capable-looking models that created a NEW Rails app
   in a subdirectory instead of building in the working dir. They did substantial work but violated the
   harness contract (each sprint accumulates in project/). A future harness could detect a nested Gemfile
   and either adopt it or re-prompt; for now scored as DNF.
2. **No-op / near-empty responses** (gpt_oss_120b, and the local qwen): the model returns almost nothing
   per sprint through opencode, so the app never grows. Distinct from a crash — exit=0 but no work.

Net: Wave 5 adds 0 models to the ranking. Final v4 field = 30 scored models (Waves 1-4 + assortment).
