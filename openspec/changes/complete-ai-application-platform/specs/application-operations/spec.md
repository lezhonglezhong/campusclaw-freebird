## MODIFIED Requirements

### Requirement: Docker Compose startup
The project SHALL provide Docker Compose configuration that starts the application and declares the server-side environment configuration needed by the application. Its Dockerfile SHALL use the explicit, pullable `docker.m.daocloud.io/library/python:3.13-slim` base-image reference, preserving the upstream Python `3.13-slim` version tag. `TOKEN_SIGNING_SECRET` SHALL be required at application startup. A source-controlled `.env.example` SHALL name the variable and provide only a non-secret placeholder or explanatory value; the Compose file and repository SHALL not contain a real authentication secret. Configuration validation MAY use a temporary command-line value, for example `TOKEN_SIGNING_SECRET=test-only-secret docker compose config`.

#### Scenario: Application starts with Docker Compose
- **WHEN** an operator starts the project with Docker Compose and supplies required environment values
- **THEN** Docker Compose starts the application service

#### Scenario: Operator waits for application readiness
- **WHEN** an operator starts the project with `docker compose up --build -d --wait`
- **THEN** the command waits for the configured healthcheck before the operator requests `GET /health`

#### Scenario: Base image is available through the selected proxy
- **WHEN** an operator builds the Compose service on the target server
- **THEN** Docker pulls `docker.m.daocloud.io/library/python:3.13-slim` and proceeds without requiring Docker Hub connectivity

## ADDED Requirements

### Requirement: Connector deployment configuration
The deployment SHALL accept PLATFORM_CONNECTORS_JSON with approved HTTP/MCP definitions and server-side credential references. A separate read-only demo tools service and example configuration SHALL be provided to demonstrate real external HTTP and MCP calls without private third-party credentials. The updated PDF SHALL distinguish controlled tests, real model calls and interoperability limitations.

#### Scenario: Start the demonstration connector service
- **WHEN** the operator starts the tools demonstration service and configures its endpoints
- **THEN** a teacher can enable its HTTP and MCP connectors and users can execute their selected tools

