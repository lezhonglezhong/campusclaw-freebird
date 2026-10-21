# Proposal

## Why

The verification report found a working class-scoped knowledge assistant but missing multiple AI applications, managed prompt templates, uploaded/executable skills, and external/MCP tools. The user requests implementation of those gaps followed by an updated evidence-backed PDF report.

## What Changes

- Add a Chinese application workspace with writing, study-planning and exercise-generation applications alongside existing grounded knowledge Q&A.
- Add class-scoped teacher-managed prompt templates with explicit input/audience variables, selection and preview.
- Add built-in and uploaded declarative JSON skills, validated bounded sequential prompt steps, full-manifest injection and visible execution records; never execute uploaded shell/Python code.
- Add deployment-configured HTTP and MCP Streamable HTTP connectors, teacher class enablement, discovery, selected-tool execution and bounded LLM tool-call/result continuation.
- Add isolated integration and browser acceptance, deployment examples, captured request/response evidence and update the PDF honestly.
- Correct stale authentication-secret references in existing specifications.
- Reflect the user clarification that this is the individual-project stage in the report, README, AGENTS and topic documents; future collaboration reuses completed capabilities.

## Capabilities

### New Capabilities
- `ai-application-workspace`: applications, prompt templates, knowledge binding and execution records.
- `declarative-skills`: built-in/uploaded skills and step execution.
- `external-tool-connectors`: external HTTP and MCP discovery and tool invocation.

### Modified Capabilities
- `application-operations`: new connector configuration and correct required token secret.
- `user-authentication`: align secret requirement with existing JWT Bearer implementation.

## Impact

Additive SQLAlchemy tables and Flask APIs; separate workspace page preserves `/api/ask` and existing materials UI contracts. Existing gateway settings are reused. New code validates tool JSON schemas, isolates class/user-owned records and avoids secrets in traces. A separate read-only demonstration service exercises actual HTTP/MCP; it is not a substitute for arbitrary third-party interoperability. Report remains in docs. No remote Git push is requested.
