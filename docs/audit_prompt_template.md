# Standardized Model Audit Prompt Template

Use this for every new model added to the benchmark, so results are comparable. Consistency is more important than any single clever observation.

---

## Usage

Paste the template below as the prompt to a general-purpose agent with file-read access. Replace `<MODEL_SLUG>` with the model's slug. Verify the output has all 8 scored dimensions plus the verification section before accepting the tier.

---

## The prompt

```
Audit the benchmark output for model <MODEL_SLUG>. Project lives at
/mnt/data/Projects/llm-coding-benchmark/results/<MODEL_SLUG>/project/

## Source of truth for RubyLLM API claims

Before classifying ANY method call as "hallucinated" or "wrong", verify against
the real RubyLLM 1.14.1 gem source. Read the chat + message classes:

- /home/akitaonrails/.local/share/mise/installs/ruby/4.0.2/lib/ruby/gems/4.0.0/gems/ruby_llm-1.14.1/lib/ruby_llm/chat.rb
- /home/akitaonrails/.local/share/mise/installs/ruby/4.0.2/lib/ruby/gems/4.0.0/gems/ruby_llm-1.14.1/lib/ruby_llm/message.rb

Key facts about RubyLLM 1.14.1 (DO NOT guess — grep the source):

- `RubyLLM.chat(model: nil, provider: nil, assume_model_exists: false, context: nil)`
  returns a Chat instance — this is the top-level entry point.
- `RubyLLM::Chat.new(model:, provider:, assume_model_exists:, context:)` is also
  a valid public constructor (some models use it).
- `Chat#ask(message = nil, with: nil, &block)` is real.
- `Chat#add_message(message_or_attributes)` takes ONE positional arg. Ruby parses
  `chat.add_message(role: :user, content: "x")` as `chat.add_message({role:, content:})`,
  which works — it's passed to `Message.new(options)`. Do NOT flag this as a kwargs bug.
- `Chat#complete(&block)` is real (used internally by `ask`, but public).
- `Chat#with_instructions(text, append:, replace:)` is real — this is how you set
  system prompts.
- `Chat#reset_messages!` is real.
- `response.content` returns the assistant text. `response.text` does NOT exist.
- `RubyLLM::Client`, `RubyLLM::Chat.new.with_model { }` block form, `chat.send_message`,
  `chat.user(...)`, `chat.assistant(...)`, `RubyLLM.chat(messages: [...])` batch form
  all DO NOT EXIST. Flag these as hallucinated.

## The benchmark prompt's explicit deliverables

(This is what the model was asked to produce. Score against THIS, not against
what you think a good Rails app should look like.)

1. Rails app using newest Ruby + Rails from mise
2. No ActiveRecord, Action Mailer, or Active Job
3. SPA mimicking ChatGPT-like interface
4. Tailwind CSS
5. Hotwire + Stimulus + Turbo Streams
6. Componentize via Rails partials (no single-file CSS/JS dumps)
7. `OPENROUTER_API_KEY` via env var, sourced from ~/.config/zsh/secrets
8. No secrets in source files, .env, Dockerfile, compose, logs, or README
9. RubyLLM (gem name `ruby_llm`, not `ruby-openai` or `rubyllm`) configured for
   OpenRouter + latest Claude Sonnet
10. Minitest unit tests for each component
11. Brakeman, RuboCop, SimpleCov, bundle-audit for CI
12. Dockerfile (functional, not placeholder)
13. docker-compose configuration (REQUIRED — don't ship only Dockerfile)
14. README explaining what it does, setup, run locally (NOT the stock Rails
    "This README would normally document..." template — that's a failure)
15. Stay in workspace root (don't create nested `chat_app/` subdir)

## Audit dimensions — score each per its weight, total 100

1. **Deliverable completeness** (0-25) — The prompt listed specific artifacts.
   Check each:
   - Dockerfile present AND has a valid Ruby version. Both Ruby 4.0.x (current
     stable) and Ruby 3.4.x (older LTS) are acceptable. Penalize only genuinely
     broken versions (e.g. Ruby 5, Ruby 2.x) or non-numeric placeholders.
   - docker-compose.yml present. Missing = -5.
   - README has actual content (NOT the stock "This README would normally document"
     template). Stock template = -5.
   - Gemfile includes: ruby_llm, turbo-rails, stimulus-rails, tailwindcss-rails,
     brakeman, rubocop (or rubocop-rails-omakase), simplecov, bundle-audit.
     Each missing = -1. Using `ruby-openai` or `rubyllm` instead of `ruby_llm` = -5.
   - Routes + controllers + views present and non-trivial.
   - Tests folder with at least one test file.

2. **RubyLLM integration correctness** (0-20) — Verified against the gem source
   above. Entry, send, response extraction, multi-turn approach, system prompt.
   - Hallucinated entry class (`RubyLLM::Client.new`, `Openrouter::Client`, etc.): -15
   - Wrong response accessor (`response.text` instead of `.content`): -3
   - Invented fluent DSL methods (`c.user`, `c.assistant`): -5
   - Invented batch signature (`RubyLLM.chat(messages: [...])`): -10
   - No multi-turn support at all (one-shot): -3
   - No system prompt via `with_instructions`: -2
   - Correct entry + ask + content + real multi-turn pattern: full marks

3. **Test quality** (0-15) — Read the actual test files.
   - Do tests EXERCISE the LLM path (not just constants/blank guards)? If no: -10
   - Do they mock with real tools (WebMock, mocha, FakeChat matching real API)? If no: -3
   - Do they mock the HALLUCINATED API (tests pass green against a bug)? If yes: -5
   - Cover error paths (API failure, missing env)? -3 if no
   - Just counting test methods doesn't score — quality over count.

4. **Error handling** (0-10) — Rescue blocks around LLM calls, missing API key
   preflight, user-visible degraded UI. No rescue = LLM hiccup = 500 page.

5. **Persistence / multi-turn state** (0-10) — Session cookie (good, up to ~4KB),
   Rails cache (better, needs shared store for multi-worker), Singleton (bad,
   process-local, lost on restart), class variables (bad), no persistence (demo-only).

6. **Hotwire/Turbo/Stimulus** (0-10) — Real Turbo Streams for messages (not just
   `fetch` + innerHTML). Stimulus controllers (auto-scroll, composer, form state).
   Partial decomposition. Broadcast support = bonus.

7. **Architecture** (0-5) — Service object separation from controllers, PORO vs
   AR-like wrapper, view partial decomposition. Avoid code dumps in controllers.

8. **Production readiness** (0-5) — Would this deploy? Multi-worker safe? No
   XSS (especially `sanitize: false` on LLM output), no leaked secrets, no
   committed `.env`, CSRF not disabled globally.

## Required output sections

A. **Quick summary line** (1 sentence).
B. **Scores** per dimension with 1-line justification each (exact file:line refs
   when claiming bugs).
C. **Total score / 100**.
D. **Practical tier**:
   - **A (80-100)**: ship as-is or with trivial (<30 min) patches.
   - **B (60-79)**: 1-2 hours to ship. Architecture is sound, minor gaps.
   - **C (40-59)**: major rework needed. Core bugs or missing deliverables.
   - **D (0-39)**: throw away or use only for architectural inspiration.
E. **Verification section** — for every API call you claim is hallucinated,
   show the grep result from the gem source that proves it. If you can't prove
   it, call it "unverified, likely correct."
F. **One killer strength** + **one killer weakness**.

Under 800 words. No speculation — code excerpts + gem source grep only.
```

---

## Notes on why this prompt exists

1. Earlier audits contradicted each other on `chat.add_message(role:, content:)`.
   Some called it a kwargs bug; some said it worked. The source-of-truth
   verification step prevents this.

2. The original tier rubric (Tier 1/2/3 from `success_report.md`) weighted
   RubyLLM correctness as dominant. That's wrong — it's only 20/100 on the
   holistic rubric. A model can hallucinate RubyLLM and still deliver 60% of
   the prompt's value (Gemini 3.1 Pro, DeepSeek V3.2). A model can get RubyLLM
   perfect and deliver 40% (DeepSeek V4 Pro with stock README + missing compose).

3. The prompt verification checklist is copy-pasted verbatim from
   `prompts/benchmark_prompt.txt`. If the benchmark prompt changes, update
   this template to match.
