# Spec Delta

## Purpose

Makes the application deployable with Docker Compose and observable through a lightweight health endpoint.

## ADDED Requirements

### Requirement: Docker Compose startup
The project SHALL provide Docker Compose configuration that starts the application and declares the server-side environment configuration needed by the application. `SESSION_SECRET` SHALL be required at application startup. A source-controlled `.env.example` SHALL name the variable and provide only a non-secret placeholder or explanatory value; the Compose file and repository SHALL not contain a real authentication secret. Configuration validation MAY use a temporary command-line value, for example `SESSION_SECRET=test-only-secret docker compose config`.

#### Scenario: Application starts with Docker Compose
- **WHEN** an operator starts the project with Docker Compose and supplies required environment values
- **THEN** Docker Compose starts the application service

### Requirement: Health endpoint
The application SHALL expose unauthenticated `GET /health`, require no request fields, and return HTTP 200 with at least `{ "status": "ok" }` when the application is running and able to serve health checks. It SHALL not return credentials, configuration, or material data.

#### Scenario: Health check request
- **WHEN** a client sends `GET /health` to a running application
- **THEN** the application returns a successful response
