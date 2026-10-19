# Company-assisted evidence beyond an API

This is a review protocol, not a conclusion about Genesys or an instruction to contact anyone. The company can provide evidence privately to an independent reviewer under an appropriate confidentiality arrangement.

## 1. Bind the demonstration to an artifact

Request the exact model configuration, tokenizer, weight files, inference software/version and deployment configuration used for an offline demonstration. Have the reviewer compute SHA-256 hashes locally. A filename, vendor-supplied hash or screenshot alone is not an independent observation.

On reviewer-controlled hardware:

1. Record artifact hashes, machine/GPU inventory, software versions and start time.
2. Deny outbound connectivity, including host-side services, and observe network traffic. A container flag on a vendor-controlled host is insufficient assurance.
3. Load the artifacts while the reviewer observes local resource allocation and execution.
4. Run fresh, previously undisclosed prompts and the frozen forensic panel. Choose an output budget compatible with the same settings.
5. Compare with a contemporaneous endpoint session, accounting for documented quantization and serving differences.
6. Preserve logs, hashes, operator notes and any deviations. Describe exactly which requests were shown to execute offline.

Supported conclusion: possession and local execution of those artifacts at that time. Not supported: independent training, ownership, legality of acquisition, or proof that every public request uses those artifacts.

## 2. Inspect model ancestry with weight access

Start with exact file/tensor equality, architecture, tensor shapes, tokenizer vocabulary and special-token IDs against *named and versioned* candidates. Re-serialization can change file hashes while leaving tensors identical, so tensor-level comparison may be needed. Never load untrusted pickle-based weights through a deserializer merely to inspect them; prefer non-executing formats and isolated review tooling.

For modified weights, assess quantization-aware comparisons and research methods such as [AWM](https://github.com/LUMIA-Group/AWM) or [LLM-Biometrics](https://github.com/OPTML-Group/LLM-Biometrics). Pin their versions and validate on known same-model, derivative and independent controls before interpreting the target. This kit deliberately does not reimplement or claim to validate these methods.

Document candidate coverage, alignment assumptions, transformations and uncertainty. A positive ancestry finding is not a finding of unauthorized use. A negative comparison only excludes the relationships that the validated method can detect against the examined candidates.

## 3. Reconcile the development history

| Requested evidence | Cross-check | Limit |
|---|---|---|
| Intermediate checkpoints across training | Local hashes, temporal progression, evaluation changes | Someone else's checkpoints can also be copied |
| Training code and experiment history | Dated commits, external CI/storage records, configuration consistency | A repository alone can be reconstructed |
| Optimizer states and logs, where retained | Consistency with checkpoints, dimensions, steps and claimed training configuration | Plausibility is not exclusive authorship |
| Compute and storage records | Independently corroborated provider/job records against dates and scale | Compute expenditure does not prove which model was trained |
| Starting weights, teachers and datasets | Declared origin, releases, agreements, transformation history | Missing records leave claims unresolved |
| Rights to distribute the resulting model | Contracts/licenses and documented chain of acquisition reviewed by the appropriate specialist | Behavioral fingerprints cannot establish these rights |

Ask the company to distinguish **trained from scratch**, **continued pretraining**, **fine-tuned**, **distilled**, **merged**, **licensed**, and **hosted** claims. Several can be legitimate parts of the same product. A precise, verifiable claim is more useful than “proprietary technology.”

## 4. Record the outcome without overclaiming

Use an evidence ledger with: claim, artifact/session, independent observer, method, controls, supported finding, unresolved alternatives and reproducible file/hash references.

Possible outcomes include “local execution observed,” “weight relationship consistent with candidate X,” “documented licensed base,” “training history corroborated in these respects,” or “origin remains unresolved.” Refusal or inability to provide proprietary artifacts limits assurance; it is not proof of theft.
