# application-operations Specification

## Purpose

Makes the application deployable with Docker Compose and observable through a lightweight health endpoint.

## Requirements

### Requirement: Docker Compose startup
The project SHALL provide Docker Compose configuration that starts the application and declares the server-side environment configuration needed by the application. Its Dockerfile SHALL use the explicit, pullable `docker.m.daocloud.io/library/python:3.13-slim` base-image reference, preserving the upstream Python `3.13-slim` version tag. `SESSION_SECRET` SHALL be required at application startup. A source-controlled `.env.example` SHALL name the variable and provide only a non-secret placeholder or explanatory value; the Compose file and repository SHALL not contain a real authentication secret. Configuration validation MAY use a temporary command-line value, for example `SESSION_SECRET=test-only-secret docker compose config`.

#### Scenario: Application starts with Docker Compose
- **WHEN** an operator starts the project with Docker Compose and supplies required environment values
- **THEN** Docker Compose starts the application service

#### Scenario: Operator waits for application readiness
- **WHEN** an operator starts the project with `docker compose up --build -d --wait`
- **THEN** the command waits for the configured healthcheck before the operator requests `GET /health`

#### Scenario: Base image is available through the selected proxy
- **WHEN** an operator builds the Compose service on the target server
- **THEN** Docker pulls `docker.m.daocloud.io/library/python:3.13-slim` and proceeds without requiring Docker Hub connectivity

### Requirement: Health endpoint
The application SHALL expose unauthenticated `GET /health`, require no request fields, and return HTTP 200 with at least `{ "status": "ok" }` when the application is running and able to serve health checks. It SHALL not return credentials, configuration, or material data.

#### Scenario: Health check request
- **WHEN** a client sends `GET /health` to a running application
- **THEN** the application returns a successful response
