# Cross-model document review protocol

## Purpose

This workflow asks the configured Codex and Claude models to review the same local document with the same brief and Skill context. It supports revision decisions. It does not prove that a document, claim, citation, or research design is correct.

## Input boundary

- Accept `.md`, `.markdown`, `.txt`, and `.docx` documents.
- Read the document locally.
- Disable model tools and browsing during the review call.
- Do not supply expected findings or another model's answer.
- Record document, brief, model-file, prompt, and Skill-context hashes.
- Keep the document and result directory outside the public release repository.

Codex calls use the local Codex CLI login state. Claude calls use the local Claude CLI login state. The workflow does not require an API key in the repository.

The runner checks both CLI login states before model calls. Claude Desktop login does not necessarily provide a Claude CLI login. If the CLI is not logged in, the run stops and directs the user to `claude auth login`.

## Same-task rule

Every selected model receives the same document text, review brief, Skill context, response schema, and issue limit. The runner records requested model IDs and provider-reported model usage when available.

## Provider-balanced synthesis

The synthesis does not count each model as one vote. Three Codex models therefore do not outvote one Claude model.

Issues are joined only when models anchor them to the same exact quote, or when one quoted anchor contains the other and the shorter normalized quote has at least 24 characters. The problem descriptions must also share at least 10% of their non-trivial normalized terms. This second check prevents different criticisms of the same sentence from being treated as agreement. Unanchored semantic similarities are not merged automatically.

Findings are reported as:

- `cross_provider`: the cluster contains Codex and Claude;
- `codex_family`: the cluster contains at least 2 Codex models and no Claude model;
- `model_specific`: the cluster does not meet either condition.

Different severity values remain visible. Repair actions are retained by model. The synthesis does not choose a winning verdict or repair.

## Status boundary

`MULTI_PROVIDER_REVIEW_COMPLETE` means all selected model calls completed and at least 2 providers returned schema-valid output. It does not mean the document passed review.

`REVIEW_INCOMPLETE` means a call failed or fewer than 2 providers completed. Existing findings may still be inspected, but they are not a complete multi-provider run.

Before changing a document, a person must check each proposed issue against the document, available sources, the research brief, and any supervisor comments.
