# Proposal

## Why

The deployed service retrieves the class-A material titled `物理定理` and its entire body `1241241`, yet `POST /api/ask` answers `资料中未找到相关内容` for “物理定理材料的内容是什么”. The chat model treats a request to report source text as a conceptual question, so a correct retrieval still produces a false no-evidence answer.

## What Changes

- Treat a complete, short, authorized source body as sufficient evidence when the question explicitly names its material and asks what that material's content or original text is.
- If the chat provider incorrectly declares such evidence insufficient, return the literal source text with its material title and traceable citation.
- Keep the existing model answer path for concept explanations, summaries, long or incomplete sources, and unrelated questions. Do not infer a theorem from a title or numeric body.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `grounded-knowledge-answering`: distinguish direct source-content questions from unsupported conceptual questions when the provider claims insufficient evidence.

## Impact

`campusclaw/knowledge_api.py`, focused ask tests, README, and GPU3 service. No new provider call, schema migration, credential change, or retrieval-scope expansion.
