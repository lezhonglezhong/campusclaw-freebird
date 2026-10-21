# external-tool-connectors Specification

## Purpose

Connect classroom applications to deployment-approved external HTTP and MCP tools with discovery, scoped availability, validated calls and auditable model continuation.

## Requirements

### Requirement: Configured and class-enabled external tools
Operators SHALL configure approved connector identifiers, labels, HTTP/MCP type, fixed endpoints and optional environment credential references outside user input. Teachers SHALL enable or disable configured connectors for their class. Students SHALL discover and select only enabled tools. HTTP connectors SHALL have an explicit JSON input schema and send validated JSON arguments to the configured endpoint. No browser request SHALL supply arbitrary URLs or credentials. Redirects SHALL not be followed; request, response and network time limits SHALL be enforced.

#### Scenario: Use an HTTP tool
- **WHEN** a teacher enables a configured HTTP connector and a student selects it
- **THEN** valid model arguments invoke that endpoint and its result returns to the model as a tool message

### Requirement: MCP Streamable HTTP tool integration
The system SHALL support MCP 2025-06-18 Streamable HTTP initialization, version negotiation, initialized notification, tools/list with bounded pagination, and tools/call. It SHALL support JSON and POST SSE response forms, preserve session and version headers, correlate request identifiers, and reject unsupported protocol versions or invalid schemas. HTTP 202 notifications SHALL be accepted. Credentials SHALL remain server-side. Stdio, OAuth provisioning and server-initiated sampling are outside this change.

#### Scenario: Discover and execute an MCP tool
- **WHEN** an enabled server returns a valid tool definition
- **THEN** its name, description and input schema are mapped to a model function definition and selected calls use MCP tools/call with name and arguments

#### Scenario: Protocol or server error
- **WHEN** a server fails, returns an unsupported version, invalid response or isError tool result
- **THEN** execution records the failure and does not report a successful answer

### Requirement: Bounded model tool loop
The model request SHALL include only selected allowed function definitions in tools and tool_choice=auto. A tool-call response SHALL be appended as an assistant message, followed by one role=tool result per call with the corresponding tool_call_id. Arguments SHALL pass JSON-schema validation before external invocation. Unknown names, duplicate call identifiers and invalid arguments SHALL fail without execution. At most four tool invocations per run and three chat rounds per skill step SHALL be allowed. Missing or empty final content SHALL fail.

#### Scenario: Model consumes an external result
- **WHEN** a model requests a selected tool and returns a final answer after the result
- **THEN** the next request contains the assistant tool_calls and matching tool result and the trace captures both model exchanges

#### Scenario: Stop a looping model
- **WHEN** the model exceeds the invocation or round limit
- **THEN** the run fails with a stable error and no further external invocation occurs
