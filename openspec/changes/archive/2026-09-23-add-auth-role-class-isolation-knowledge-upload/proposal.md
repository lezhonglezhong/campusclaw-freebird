# Proposal

## Why

CampusClaw needs a secure, class-scoped foundation before teaching materials can be shared through its knowledge base. Authentication, authorization, and server-enforced class isolation prevent users from accessing or changing material outside their role or class.

## What Changes

- Add account/password authentication for teacher and student users, including redirecting unauthenticated users from protected pages to the login page.
- Add role-based authorization that allows only teachers to upload teaching materials and rejects student upload API requests.
- Add server-side class isolation for teaching-material access so users cannot retrieve materials belonging to another class.
- Add teacher material upload to the knowledge base and class-scoped material listing that includes successfully uploaded records.
- Add browser-selectable `.txt` and `.md` material-file uploads with a teacher-provided material name while retaining the established JSON upload contract for compatibility.
- Keep browser text-entry upload alongside file selection, and let authorized class members download material content.
- Let a teacher delete material belonging to that teacher's session class together with its stored content.
- Add class-scoped material-name search and show a human-readable class name (such as A or B) without exposing client control over class ownership.
- Seed representative A- and B-class teacher and student accounts, classes, and teaching-material records so login, role, class-boundary, and B-class workflows can be verified in a fresh local deployment.
- Require password hashes rather than plaintext passwords, server-only environment variables for secrets, Docker Compose startup, and a `GET /health` health endpoint.
- Use the verified public registry-proxy reference `docker.m.daocloud.io/library/python:3.13-slim` for the Compose build base image because this deployment's Docker daemon cannot reach Docker Hub directly; retain the upstream Python version/tag in that reference.
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
- Cross-class material sharing, multi-class enrollment, teacher account administration, and teacher selection of another class for an upload.
- External knowledge-base services, vector retrieval, embeddings, RAG, and material question answering.

## Impact

- Adds authentication, authorization, class membership, material/knowledge-base persistence, and protected web/API routes.
- Extends the upload API with safe text/Markdown file input, and extends class-scoped material queries with name-only search and display class names.
- Adds class-scoped material download and teacher-only deletion contracts, including browser controls and seed content that is downloadable in a fresh deployment.
- Requires container orchestration configuration, an explicitly documented pullable Python base-image reference, a health endpoint, password-hashing support, and server environment configuration for secrets.
