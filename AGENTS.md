# Agent instructions

Read CLAUDE.md for the repository's benchmark, evidence-preservation and secrets rules.

Current local LLM setup, serving, model archive, and host operations are
documented in `../my-omarchy-config-next/docs/machine/`. Put new local setup
instructions there; keep benchmark methodology, results, and immutable evidence
here. Historical local setup pages in this repository should point to their
current machine documents.

## Required end-of-task cleanup

At the end of every completed benchmark, forensic run, validation or implementation task, perform the scoped cleanup procedure in docs/CLEANUP.md before reporting completion. This is a standing user instruction. Preserve test results, analysis and evidence. Report what was removed and what remains intentionally retained. A paused run is not a completed run.

## Model archive is permanent

Before downloading weights for any test or serving run, check the NAS model archive described in docs/HF_MODEL_ARCHIVE.md. Reuse a verified archived checkpoint when its model, revision and quantization match the planned run; do not download the same weights again. Preserve the archive copy when staging a model elsewhere.

When a newly tested model proves useful for future testing or serving, retain its weights in the NAS archive and record its source, exact revision, quantization, verification status and test evidence in the archive manifest or documentation.

Never delete archived model weights, partial downloads, manifests or provenance from the NAS without the user's explicit approval. This restriction also applies during cleanup, disk-space recovery and benchmark reruns. If space is insufficient, report the constraint and request approval for any proposed archive deletion.

## Model source trust gate

Before starting a new model download, check that the model page and publisher have credible provenance. Inspect the pinned repository's file list, license, model card, upstream weight lineage, chat template and any executable helpers or remote-code requirements. Record the evidence and unresolved risks in the archive documentation. Hash verification proves transfer integrity, not that the source is trustworthy. Do not execute downloaded scripts or deploy a checkpoint with unreviewed embedded instructions into an agent that has access to user files or secrets. Use an isolated, credential-free trial for uncertain sources.
