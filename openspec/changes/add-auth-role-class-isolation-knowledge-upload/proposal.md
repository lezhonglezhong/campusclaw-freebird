# Proposal

## Why

CampusClaw needs a secure, class-scoped foundation before teaching materials can be shared through its knowledge base. Authentication, authorization, and server-enforced class isolation prevent users from accessing or changing material outside their role or class.

## What Changes

- Add account/password authentication for teacher and student users, including redirecting unauthenticated users from protected pages to the login page.
- Add role-based authorization that allows only teachers to upload teaching materials and rejects student upload API requests.
- Add server-side class isolation for teaching-material access so users cannot retrieve materials belonging to another class.
- Add teacher material upload to the knowledge base and class-scoped material listing that includes successfully uploaded records.
- Seed representative teacher, student, class, and teaching-material records so the login, role, and class-boundary workflows can be verified in a fresh local deployment.
- Require password hashes rather than plaintext passwords, server-only environment variables for secrets, Docker Compose startup, and a `GET /health` health endpoint.
- Use the project's local `Material` persistence and managed local content storage as the course project's knowledge-base implementation; external knowledge-base services, embeddings, and retrieval are not introduced.

## Capabilities

### New Capabilities

- `user-authentication`: Account/password login, protected-page access handling, and secure credential and secret handling.
- `role-based-material-upload`: Teacher-only material upload authorization and knowledge-base persistence.
- `class-scoped-material-access`: Server-enforced class boundary for material listing and retrieval.
- `application-operations`: Docker Compose startup and application health checking.

### Modified Capabilities

- None.

## Non-Goals

- Knowledge-base retrieval question answering or a conversational assistant.
- Assignment submission, grading, feedback, or grade management.
- Single sign-on, third-party identity integration, production high availability, or horizontal scaling.
- Cross-class material sharing, multi-class enrollment, and teacher account administration.
- External knowledge-base services, vector retrieval, embeddings, RAG, and material question answering.

## Impact

- Adds authentication, authorization, class membership, material/knowledge-base persistence, and protected web/API routes.
- Defines an upload API that must reject unauthorized student requests and class-scoped material query behavior.
- Requires container orchestration configuration, a health endpoint, password-hashing support, and server environment configuration for secrets.
