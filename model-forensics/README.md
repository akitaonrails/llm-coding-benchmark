# Genesys model forensics

A reproducible, standalone kit for investigating **observable model identity and stability**. It compares Genesys with explicit reference endpoints and with its own earlier sessions. It never assigns an ownership verdict or a probability that a company stole or independently trained a model.

**Implementation status:** collector and analysis tested against local HTTP fixtures and synthetic reference data. Live compatibility checks and the first exploratory panel started on 2026-10-08; see [operational notes](OPERATIONS.md). The v4.1 results are not inputs to this experiment.

Start with the [experiment plan](PLAN.md), [collector and analysis](kit.py), [probe definitions](probes.py), [configuration](config.example.json), [verification tests](tests/test_kit.py), and [company-assisted provenance checklist](PROVENANCE.md). Research links and limitations are in the plan.

## Findings and feasibility

Read [FINDINGS.md](FINDINGS.md) for observed evidence, verified GPT-4o versus GPT-5.6 Sol API pricing, model-size disclosures, and explicitly hypothetical gpt-oss distillation effort/cost estimates.

## Stronger follow-up

**Current investigation:** [gpt-oss output forensics and reproduction](oss/README.md), with a reference-validation gate before collecting Genesys. GPT-4o collection is finished/stopped; see [updated findings](FINDINGS.md).

The [confirmatory GPT-4o experiment](confirmatory/README.md) adds 1,024 generated tokenizer strings, reference-only rare-error discovery, prompt perturbations, GPT-4o wrapper controls, a calibration gate, and a temporal repeat. It has its own frozen manifests and results; it does not replace the pilot.

## What is measured

The default seed creates 62 prompts in 18 families, with entire families assigned to exploratory or holdout analysis. Every request is a fresh, single-turn conversation with the same system prompt and a frozen sampling policy. Randomization orders the prompts and interleaves endpoints within each replicate.

| Channel | Concrete probes | Analysis | What it cannot establish |
|---|---|---|---|
| Categorical preferences | Numbers, letters, colors, shapes, Portuguese and Spanish words; permuted choice order | Empirical answer distributions and total-variation distance | Similar preferences do not demonstrate shared weights or a teacher/student relationship |
| Exact answers and errors | Modular arithmetic, character counts, list indexing, binary conversion | Answer agreement, correctness, and same-wrong-answer frequency | Shared correct answers mostly demonstrate task competence; common mistakes can come from common data |
| Copying behavior | Combining marks, visually similar scripts, emoji sequences, code punctuation | Exact string agreement and errors | A copying quirk alone does not identify embeddings or training origin |
| Tokenization patterns | Base/doubled ASCII, CJK, code, Arabic, spaces, emoji strings | Difference in provider-reported prompt counts, then differences between endpoints | Matches support a common tokenization pattern, not shared ancestry |
| Session stability | Repeat the same frozen panel at separated times | Compare session/model pairs and inspect per-probe distributions and failures | Changes alone do not prove routing, proxying, or model substitution |

These are deliberately short fingerprints, not harder versions of the coding benchmark. They are a starter panel with limited discriminatory power. Strong attribution would require demonstrated separation on documented controls, additional independent evidence, and a fresh confirmatory panel.

## Install and verify

Python 3.10+ on Linux/macOS; Python standard library only. No pip packages, benchmark runner, Docker, OpenCode, credential-file parsing, or global configuration changes are required.

From the repository root:

```sh
python3 -m unittest discover -s model-forensics/tests -v
python3 model-forensics/kit.py --help
```

The tests use an ephemeral loopback HTTP server and synthetic observations. They make no vendor calls and require no real credentials.

## Configure the panel

```sh
cp model-forensics/config.example.json model-forensics/config.local.json
```

The example targets the same **House** endpoint model identifier as v4.1: `genesys-pi-house`. The older `lua-forensics` scripts often targeted **Enterprise**, so do not combine their observations with this experiment or treat those names as interchangeable.

The collector reads keys **only from the named environment variables**. For Genesys, supply `LUA_API_KEY` through your normal secret manager or already-authenticated shell. Do not put values in JSON, command arguments, URLs, logs, or checked-in files. For a local server that ignores authentication, a non-secret dummy environment value is sufficient. The kit neither reads nor changes subscription CLI credentials.

Add reference entries to the `models` array using this shape, replacing the example endpoint and ID before planning:

```json
{
  "label": "reference-a",
  "base_url": "https://YOUR_REFERENCE_ENDPOINT/v1",
  "model": "EXACT_PROVIDER_MODEL_ID",
  "key_env": "REFERENCE_API_KEY",
  "revision_note": "Record exact revision, hosting provider and known lineage here"
}
```

Use endpoints implementing non-streaming OpenAI-compatible `/chat/completions`, with `max_tokens`, string `message.content`, and `finish_reason`. The default `temperature: null` omits temperature: Genesys House rejects this parameter and reports fixed sampling. A numeric value explicitly requests that temperature. Omission across endpoints does not equalize their sampling defaults; reports flag this limitation. Unsupported parameters cause a recorded error, not a silent fallback. Native Codex/Claude subscription runners are not used: their hidden prompts and agent tools would change the experiment. An endpoint that only supports a different API needs a separately tested adapter and a new protocol version.

**Initial reference-panel design:**

| Role | Candidates to obtain | Reason |
|---|---|---|
| Target | Genesys House; optionally Enterprise as a separate label | Keep the actual tested product identity explicit |
| Shared-tokenizer candidates | GPT-4o and gpt-oss checkpoints where accessible | Investigate the earlier o200k hypothesis without assuming ancestry |
| Alternative families | Available Qwen, DeepSeek, Llama, Kimi and GLM revisions | Test a broader candidate set; do not treat nationality as a technical signal |
| Same-model positive control | One exact open-weight checkpoint hosted twice, with documented hashes | Check sensitivity to serving wrappers and provider differences |
| Relationship control | A documented base and its documented fine-tune | Measure whether this panel detects that particular derivative relationship |
| Independent negative controls | At least two documented independently trained bases | Estimate incidental similarity on this panel |

Select a small panel first. Verify currently available model IDs with the providers before freezing them; this kit intentionally does not invent current IDs or assume aliases are pinned. Prefer direct or controlled local hosting. If using an aggregator, document provider selection and fallback policy: an aggregator's routing is another unknown. Returned model strings and fingerprints are claims made by the endpoint, not attestations.

## Freeze, inspect, then collect

A pilot is **2 replicates × 62 probes = 124 requests/model**. A full session is **20 × 62 = 1,240 requests/model**. At the default requested `max_tokens=256`, the corresponding submitted completion limits total 31,744 and 317,440 tokens/model. Input tokens, reasoning accounting and actual billing are additional/provider-dependent; these are not cost estimates. Calls are serial and each has a configured socket timeout.

```sh
python3 model-forensics/kit.py plan \
  --config model-forensics/config.local.json \
  --name genesys-pilot-01 --profile pilot

# Inspect runs/genesys-pilot-01/manifest.json before issuing requests.
python3 model-forensics/kit.py collect genesys-pilot-01 --limit 4
python3 model-forensics/kit.py status genesys-pilot-01

# Continue the exact frozen schedule.
python3 model-forensics/kit.py collect genesys-pilot-01
python3 model-forensics/kit.py report genesys-pilot-01
```

`--limit` is the maximum number of *additional* requests for that invocation. Repeating `collect` resumes; it never overwrites previous observations. Each request completion prints progress. `status` can be called from a separate terminal. A partially written record may produce a validation error during simultaneous reading; repeat status after the collector completes the write. Reports should be generated between collection invocations.

Pilot results check compatibility and missingness only. Once the pilot works, freeze a full session under a new name:

```sh
python3 model-forensics/kit.py plan \
  --config model-forensics/config.local.json \
  --name session-01 --profile full
python3 model-forensics/kit.py collect session-01
python3 model-forensics/kit.py report session-01
```

Repeat as `session-02` and `session-03` at separated, recorded times using **the same config, suite seed, code and profile**. Do not tune prompts based on the holdout results. Then compare:

```sh
python3 model-forensics/kit.py report session-01 session-02 session-03
```

Separate panel subsets can be compared if probes, profile, code and generation settings match. A pilot cannot be combined with full sessions. Cross-session reports compare all pairs, including Genesys-to-Genesys; a one-model, one-session report provides coverage and signatures, but cannot identify similarity to absent references.

## Files and integrity

Everything generated stays under this directory's ignored `runs/` tree:

```text
runs/session-01/
  manifest.json       # Exact config, prompts, randomized schedule, hashes, UTC creation
  source/             # Frozen kit.py, probes.py and PLAN.md
  responses.jsonl     # Append-only hash-chained observations, timing and bounded response fields
  pending.json        # Exists only around an in-flight request
  .lock               # OS advisory lock prevents simultaneous collectors
runs/report-<manifest-hash>-<analysis-hash>/
  analysis.json       # Per-model signatures, coverage, pairwise and per-probe evidence
  report.md           # Human-readable comparison and limitations
```

The manifest captures declared model/revision notes and Python version. Responses retain text, usage, status, timings and selected endpoint metadata; reasoning text, arbitrary headers, cookies and error bodies are omitted. Exact known API key values are redacted from stored response fields. Do not execute model outputs. Inspect artifacts before sharing: model responses remain untrusted text and are not guaranteed free of unrelated sensitive content.

Code/plan changes prevent collection into an old run. To resume after an upgrade, restore the frozen source to a **separate copy of the kit**, with its tests and the matching `runs/<name>` directory; do not mix source versions in one session. Config edits do not change already-planned runs.

The SHA-256 chain detects accidental edits and inconsistent sequences. It is **not** a signature or proof against someone who rewrites the whole experiment and recalculates hashes. Publish/sign manifest and completed-chain hashes independently if adversarial custody matters. Mutable vendor aliases and server-side changes remain outside reproducibility guarantees.

## Failures and resumption

- HTTP failures, transport errors, invalid JSON/schema and oversize responses pause collection. Fix infrastructure and invoke `collect` again to proceed to the next scheduled observation. Failures remain in the dataset; there are no automatic retries.
- Empty answers, truncation and nonstandard finish reasons are retained but excluded from behavioral distributions. Valid prompt-token counts can still inform the tokenization channel. Invalid categorical answers are counted separately and excluded from categorical distances.
- An interrupted request may have reached the provider. On resume it becomes `interrupted_unknown` and is not replayed. This avoids selecting successful retries and duplicate charges for that observation.
- A torn manifest/pending/JSONL write fails closed. Preserve the damaged run and start a new named session; do not manually delete observations to make integrity checks pass.
- Changing settings or fixing an incompatible provider requires a new plan. Preserve the original pilot, including its failures.

## Interpreting evidence

`choice_tv` runs from 0 (matching empirical distributions) to 1 (disjoint). Finite samples can make the same model look different. `exact_agreement` and `shared_wrong_answer` are probabilities computed from independent draws from the *observed* distributions, not paired random seeds or confidence in ancestry. Token deltas remove only a constant template offset, not arbitrary preprocessing.

Metrics weight probe families equally. Family-bootstrap intervals are descriptive, with few families and substantial unmodeled sampling/provider uncertainty; no interval is emitted for fewer than three families. The JSON report contains per-probe coverage and distributions so missingness cannot be hidden by a single average. There is no significance test, learned attribution classifier, automatic ranking, universal cutoff, or combined provenance score.

A reasonable investigative finding is: “Genesys resembles candidate X on these held-out channels, by these distances, relative to these same-model and independent-model controls.” An equally valid finding is “the panel cannot distinguish these hypotheses.” A mismatch does not rule out an untested source or a substantially modified/distilled descendant. Capability variance, language preference, self-identification and absence of gateway headers do not prove origin.

For evidence of possession, weight ancestry or ownership, follow [PROVENANCE.md](PROVENANCE.md). The [older suite](../lua-forensics/README.md) is historical context only; its claim that a distillation necessarily retains its teacher's tokenizer is not a premise of this kit.

Additional research: [previously untested o200k-compatible candidates](CANDIDATES.md), including pinned tokenizer checks and deployment options.
