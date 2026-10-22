# Paused pending batch review

Automatic supervisor: sprint or boundary failed; preserve for batch review

Checkpoint: `results-v4/v2_nex_n2_5_mini_oss/pause-checkpoints/1792274991683017407/state.json`

- Review all models after batch before selecting resumptions.
- Archive remote launch state/logs locally before loading another model; preserve execution state/caches; weights alone may be removed if space is needed and an immutable revision is recorded.
- Restore serving configuration from this checkpoint and verify API/tool preflight.
- Verify session export succeeded; retain local OpenCode session store. Do not delete failed export evidence.
- Determine whether current sprint ended or was interrupted; preserve existing logs before continuation.
- Do not blindly rerun standard launcher: it skips existing sprint.result.json and DNF markers.
- Verify grading/injection boundary records before advancing sprint. Never repeat completed injections.
- Record any additional authorized budget separately; keep original attempt time, costs and pause artifacts.

Preserve the entire workspace, temporary files, session data and remote execution state/caches. Downloaded weights alone may be removed for space after recording an immutable revision. DNF is a queue-control marker for this budget, not a final abandonment decision.
