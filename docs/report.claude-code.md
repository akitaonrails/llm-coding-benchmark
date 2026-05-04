# Claude Code Subagent Benchmark Report

This benchmark compares three configurations of Claude Code on the same Rails chat-app prompt:

- `claude_opus_alone` — baseline, pure Opus 4.7 (no subagent delegation)
- `claude_opus_sonnet` — Opus 4.7 main + Sonnet 4.6 coding subagent
- `claude_opus_haiku` — Opus 4.7 main + Haiku 4.5 coding subagent

Same prompt as the main benchmark (`prompts/benchmark_prompt.txt`). Phase 1 only.

Runner: `claude -p --output-format stream-json --dangerously-skip-permissions`

## Summary

| Variant | Status | Time | Files | Turns | Delegations | Total Cost |
|---|---|---:|---:|---:|---:|---:|
| claude_opus_alone | completed | 662s | 1742 | 129 | 0 | $6.7394 |
| claude_opus_sonnet | completed | 606s | 1829 | 106 | 0 | $5.1309 |
| claude_opus_haiku | completed | 882s | 1984 | 136 | 0 | $7.8282 |
| claude_opus_sonnet_forced | completed | 1489s | 1892 | 43 | 0 | $5.7749 |
| claude_opus_haiku_forced | completed | 1148s | 134 | 34 | 0 | $3.4916 |
| claude_code_deepseek_v4_pro_or | completed | 1255s | 1544 | 106 | 0 | $3.3811 |
| claude_code_deepseek_v4_pro_or_sonnet | completed | 1075s | 1348 | 109 | 0 | $3.1401 |

## Per-Model Token Usage

Extracted from Claude Code's `modelUsage` field. Cost is computed server-side by the SDK.

### claude_opus_alone

| Model | Input | Output | Cache Read | Cache Create | Cost |
|---|---:|---:|---:|---:|---:|
| claude-haiku-4-5-20251001 | 890 | 24 | 0 | 0 | $0.0010 |
| claude-opus-4-7 | 139 | 43,982 | 9,311,254 | 157,202 | $6.7384 |

### claude_opus_sonnet

| Model | Input | Output | Cache Read | Cache Create | Cost |
|---|---:|---:|---:|---:|---:|
| claude-haiku-4-5-20251001 | 890 | 24 | 0 | 0 | $0.0010 |
| claude-opus-4-7 | 116 | 39,471 | 6,609,775 | 134,030 | $5.1299 |

### claude_opus_haiku

| Model | Input | Output | Cache Read | Cache Create | Cost |
|---|---:|---:|---:|---:|---:|
| claude-haiku-4-5-20251001 | 890 | 20 | 0 | 0 | $0.0010 |
| claude-opus-4-7 | 146 | 50,754 | 10,884,379 | 178,465 | $7.8272 |

### claude_opus_sonnet_forced

| Model | Input | Output | Cache Read | Cache Create | Cost |
|---|---:|---:|---:|---:|---:|
| claude-haiku-4-5-20251001 | 1,765 | 22 | 0 | 0 | $0.0019 |
| claude-opus-4-7 | 58 | 48,631 | 2,614,400 | 134,282 | $3.3625 |
| claude-sonnet-4-6 | 199 | 43,179 | 3,767,664 | 168,507 | $2.4105 |

### claude_opus_haiku_forced

| Model | Input | Output | Cache Read | Cache Create | Cost |
|---|---:|---:|---:|---:|---:|
| claude-haiku-4-5-20251001 | 2,129 | 33,518 | 5,514,016 | 143,394 | $0.9004 |
| claude-opus-4-7 | 39 | 32,266 | 1,378,651 | 175,204 | $2.5912 |

### claude_code_deepseek_v4_pro_or

| Model | Input | Output | Cache Read | Cache Create | Cost |
|---|---:|---:|---:|---:|---:|
| deepseek/deepseek-v4-pro | 69,967 | 36,380 | 4,243,584 | 0 | $3.3811 |

### claude_code_deepseek_v4_pro_or_sonnet

| Model | Input | Output | Cache Read | Cache Create | Cost |
|---|---:|---:|---:|---:|---:|
| deepseek/deepseek-v4-pro | 65,965 | 28,936 | 4,173,824 | 0 | $3.1401 |

## Delegation Details

## Comparison vs Opencode Baseline

The main benchmark runs Opus 4.7 through opencode (different runner, different harness). Cross-profile comparison is approximate since the tooling overhead and token accounting differ, but cost-per-run is directly comparable.

Reference: Opus 4.7 via opencode — ~$1.10/run, 18m, 28 tests (see `docs/success_report.md`).
