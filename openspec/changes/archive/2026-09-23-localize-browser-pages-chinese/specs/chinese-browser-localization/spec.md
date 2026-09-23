# Spec Delta

## Purpose

Make the existing CampusClaw browser login and material workflows consistently
understandable to Simplified Chinese-speaking course users without altering
their server-side behavior or security boundaries.

## ADDED Requirements

### Requirement: Simplified Chinese browser presentation

The system SHALL present all user-visible browser text on the login and
material workspace pages in Simplified Chinese. This includes page titles,
headings, form labels, buttons, material-detail labels, role/class context,
and loading, empty, success, and error messages. Product and account names
such as `CampusClaw`, API paths, and seeded account identifiers MAY remain
unchanged where they are identifiers rather than user-facing Chinese prose.

#### Scenario: User reads the login page in Chinese
- **WHEN** a visitor opens `GET /login`
- **THEN** the visible page title, sign-in instructions, account/password
  labels, and sign-in action are presented in Simplified Chinese

#### Scenario: User receives Chinese workflow feedback
- **WHEN** a user encounters an invalid login, material loading state, empty
  list, upload result, unauthorized state, or unavailable material
- **THEN** the corresponding user-visible feedback is presented in Simplified Chinese

### Requirement: Localization preserves existing browser behavior

The localization change SHALL NOT alter browser routes, API endpoint paths,
request payload keys, session-cookie handling, authenticated identity source,
role-based upload availability, class filtering, or server-side authorization
responses.

#### Scenario: Localized teacher and student workflows retain permissions
- **WHEN** a teacher and a student use the localized browser interface
- **THEN** the teacher retains the upload workflow, the student remains
  read-only, and existing server authorization outcomes remain unchanged
