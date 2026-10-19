#!/usr/bin/env python3
import json, re, time
from pathlib import Path

REPO = Path("/mnt/data/Projects/llm-coding-benchmark")
OUT = REPO / "results-v4"
COMPLETED = {"v2_glm_5_3_flash_oss","v2_swift_1_5_27b_oss","v2_qwen3_8_27b_oss",
             "v2_dsv4_flash_oss","v2_glm_4_7_flash_bf16_oss"}

models = {}
for d in sorted(OUT.glob("v2_*_oss")):
    slug = d.name
    bdir = d / "boundaries"
    boundaries = []
    if bdir.is_dir():
        for b in sorted(bdir.iterdir()):
            if not b.is_dir():
                continue
            m = re.match(r"sprint(\d+)", b.name)
            if not m:
                continue
            sprint = int(m.group(1))
            reviewer = "claude" if "-claude-" in b.name else "codex"
            has_verdict = (b / "verdict.json").is_file()
            boundaries.append({"dir": b.name, "sprint": sprint,
                               "reviewer": reviewer, "has_verdict": has_verdict})
    codex_b = sorted({x["sprint"] for x in boundaries if x["reviewer"]=="codex"})
    claude_b = sorted({x["sprint"] for x in boundaries if x["reviewer"]=="claude"})
    if slug in COMPLETED:
        mix = "codex_complete"
    elif claude_b:
        mix = "mixed_codex_then_claude"
    else:
        mix = "codex_only_so_far_pending_claude_resume"
    models[slug] = {"reviewer_mix": mix,
                    "codex_boundary_sprints": codex_b,
                    "claude_boundary_sprints": claude_b,
                    "boundaries": boundaries}

doc = {
  "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
  "description": "Per-model, per-boundary independent-reviewer provenance for the B300 open-weight v4 batch.",
  "reviewers": {
    "codex": "OpenAI Codex (codex exec); boundary transcript in boundaries/sprint<NN>-*/agent.ndjson",
    "claude": "Claude Opus 4.8; boundary dir named boundaries/sprint<NN>-claude-* with verdict/manifest/report"
  },
  "switch": {
    "date": "2026-10-19",
    "reason": "Codex security service refused the authorized sabotage-injection/grading operation (cybersecurity flag); user explicitly instructed switching the independent reviewer to Claude to complete the batch.",
    "unchanged_across_switch": ["injection plan","sabotage catalog","14-item set","severity denominator 40",
      "scoring buckets (full unprompted / 40% after reveal / 0 unresolved)","one-candidate shield/isolation","two-nudge ceiling"],
    "completed_models_wholly_codex": sorted(COMPLETED)
  },
  "models": models,
}
dest = OUT / "_b300_campaign" / "reviewer-provenance.json"
dest.write_text(json.dumps(doc, indent=2) + "\n")
print("wrote", dest)
for s, v in models.items():
    print(f"  {s:34s} {v['reviewer_mix']:34s} codex={v['codex_boundary_sprints']} claude={v['claude_boundary_sprints']}")
