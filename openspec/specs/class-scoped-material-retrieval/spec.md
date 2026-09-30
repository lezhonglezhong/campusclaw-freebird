# class-scoped-material-retrieval Specification

## Purpose

Allows authenticated users to retrieve matching teaching-material content without crossing their server-derived class boundary.

## Requirements

### Requirement: Class-scoped content retrieval
The system SHALL expose `GET /api/materials/retrieve?q=<query>` to authenticated teachers and students. It SHALL require a non-empty query, search indexed material content only after filtering by the validated session class, and return HTTP 200 with `{ "results": [ ... ] }`. An unauthenticated request SHALL return HTTP 401 with an `error` field; malformed queries SHALL return HTTP 400 without material data.

#### Scenario: User retrieves own-class content
- **WHEN** an authenticated class-A user searches text occurring in a class-A material
- **THEN** the response contains matching class-A results and no class-B data

#### Scenario: Same query cannot cross class boundaries
- **WHEN** a class-A user searches text occurring only in class-B material
- **THEN** the response returns an empty result list

#### Scenario: User retrieves Chinese content
- **WHEN** an authenticated user searches a Chinese phrase contained in an own-class material
- **THEN** the response contains that material's matching result
