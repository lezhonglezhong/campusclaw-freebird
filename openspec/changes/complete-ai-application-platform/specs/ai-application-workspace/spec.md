## Purpose
Provide a usable classroom AI application workspace with configurable prompts, bounded knowledge context and inspectable execution results for authenticated users.

## ADDED Requirements

### Requirement: Multiple usable AI applications
The system SHALL expose an authenticated application catalog and separate Chinese workspace with writing, study-planning and exercise-generation applications, plus navigation to existing knowledge Q&A. Each new application SHALL have a distinct default instruction and accept input up to 4000 characters. Unknown application identifiers SHALL return 404. Existing knowledge Q&A SHALL retain its current contract.

#### Scenario: Choose an application
- **WHEN** a signed-in student selects writing or exercise generation and submits text
- **THEN** the respective application instruction is sent to the model and its generated result is displayed

### Requirement: Managed prompt templates
Teachers SHALL create, edit and delete class-scoped templates with name, content and the supported variables {{input}} and {{audience}}. Users SHALL list and select only their class templates; built-in defaults SHALL remain available. The rendered template SHALL be included in the model messages and visible in an execution record. Invalid variables or excessive content SHALL be rejected with 400; student mutations SHALL return 403 and cross-class identifiers 404.

#### Scenario: Reuse a saved template
- **WHEN** a teacher saves a template and a same-class student selects it with audience text
- **THEN** the selected content with substituted variables is sent with the application instruction

#### Scenario: Reject cross-class template use
- **WHEN** a user submits another class's template identifier
- **THEN** the request returns 404 before any external model call

### Requirement: Bounded knowledge binding
Users SHALL optionally bind their own class knowledge to a workspace request. Such requests SHALL reuse current bounded retrieval and evidence selection, include only chosen sources, preserve source identifiers in displayed citations, and require valid citations and supported numbers in the final answer. Empty retrieval SHALL return an explicit no-evidence result without calling chat. Unbound requests SHALL not retrieve knowledge.

#### Scenario: Run with knowledge enabled
- **WHEN** a user binds knowledge and evidence is found
- **THEN** only selected class-scoped chunks reach chat and unsupported final citations trigger at most one correction before failure

### Requirement: Private execution evidence
Each valid execution SHALL store an owner- and class-scoped record with status, application, selected bindings, exact model request/response bodies, skill steps and tool arguments/results. No credentials, authorization headers or private connector URLs SHALL be stored or returned. Only the requesting user in their current class SHALL retrieve their records. Provider errors SHALL return a stable error with the record identifier; bounded steps and output sizes SHALL prevent unbounded execution.

#### Scenario: Inspect a request
- **WHEN** the owner opens a completed run
- **THEN** they can inspect rendered prompts, sources, model parameters, returned messages and executed steps

#### Scenario: Another user requests a trace
- **WHEN** another user or a user moved to another class requests a run
- **THEN** the API returns 404
