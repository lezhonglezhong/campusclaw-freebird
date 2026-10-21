# Design

## Context
See proposal.md. Existing Flask/SQLAlchemy application has a synchronous OpenAI-compatible provider, JWT authentication, class-scoped retrieval and 168 passing tests. Keep /api/ask unchanged. Existing main auth specs include obsolete Cookie/page wording as well as obsolete secret names; correct those to the deployed Bearer contract.

## Goals / Non-Goals
Deliver usable UI and APIs for all missing assessment features with inspectable exact calls. Skills are intentionally declarative prompt workflows, not arbitrary executable packages. MCP support targets the published 2025-06-18 Streamable HTTP protocol (JSON and POST SSE); stdio, OAuth and sampling are not included. No remote Git push or claim of individual authorship.

## Decisions
- Separate /apps workspace and /api/platform endpoints keep existing answer contracts and regression tests stable. Three immutable catalog applications supply distinct system instructions; templates and skill choices bind on each run through explicit form controls.
- Add PromptTemplate, UploadedSkill, ConnectorBinding and ApplicationRun tables through additive create_all. Templates/skills are class-owned; traces are also user-owned. Existing tables need no destructive migration.
- Templates use literal {{input}}/{{audience}} substitution, never eval/Jinja execution. Limit input 4000, template 8000, audience 200 characters. Skill upload is a strict JSON manifest of at most 16 KiB and 1–3 prompt steps. Inject complete manifest and execute each named instruction in order with preceding output. A prompt workflow is executable through its LLM steps; it does not imply script execution.
- Reuse knowledge retrieval and citation validation for optional binding. Use a bounded question substring for retrieval and preserve full input for generation. Unbound writing/planning can use model knowledge and returns no fabricated knowledge citations. Bound final output must satisfy original citation checks, including comparison requirements.
- Use deployment-approved fixed connector URLs with optional token_env references; teachers only toggle class enablement. Reject URL credentials/fragments, disable redirects, never accept URLs from browser/model. Only configured read-only services should be enabled; explicit selection authorizes those calls. Native HTTP tools have configured schema. MCP tools are discovered by initialize, initialized, tools/list and mapped to namespaced function names; sessions end after each run. Validate schemas/arguments with jsonschema, bound response bytes and runtime. MCP protocol references: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports and /basic/lifecycle and /server/tools.
- A new chat exchange method returns content/tool_calls and captures model request/response bodies via an injectable callback. Do not change existing answer method. Loop through selected tool calls with validated arguments; preserve assistant/tool messages. Per-run max 4 tool calls; per-step max 3 exchanges; one final citation correction if needed. Trace omits HTTP credentials and connector URLs and is visible only to its owner.
- Separate demo service provides calculator HTTP and MCP tools over actual network. Tests use independent local servers and deterministic gateway responses; live gateway tests use synthetic data. Browser acceptance uses Playwright locally, with no production content exported.

## Risks / Trade-offs
- Third-party schema/transport incompatibility → explicit supported version, JSON/SSE/session/pagination tests and clear failures, no broad interoperability claim.
- Model latency and nondeterminism → bounded steps/calls, timeouts and reproducible controlled tests plus separate live smoke.
- Trace contains user content → owner/class authorization, no public listing and bounded stored payloads; secrets never logged.
- Skill instructions can affect generated text → no arbitrary code execution, fixed authorized tools, retained knowledge citation validation.

## Migration Plan
Run tests task by task, then full suite. Build updated application and optional demo service after verification; preserve .env and persistent volumes. Additive tables survive rollback to old application. Publish updated report only after actual evidence is available. Sync delta specs, validate main specs and archive after implementation. Existing untracked unrelated docs/caches must not be staged.
