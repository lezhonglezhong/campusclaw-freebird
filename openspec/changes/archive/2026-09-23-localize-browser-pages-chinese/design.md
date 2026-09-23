# Design

## Context

The completed `add-browser-material-pages` change provides Flask HTML templates
and static vanilla JavaScript for login and material management. Its API and
authorization behaviors are already covered by tests; only presentation text
needs localization.

## Goals / Non-Goals

**Goals:**

- Translate every user-visible English phrase in the current browser pages to
  Simplified Chinese.
- Preserve DOM IDs, field names, API contracts, and workflow behavior so the
  existing client code and backend tests remain compatible.

**Non-Goals:**

- A multi-language selector, locale persistence, translation framework, or
  changes to API JSON fields and server error codes.

## Decisions

### Translate presentation strings in place

Templates and JavaScript literals will use Simplified Chinese directly. This is
the smallest solution for a single-language course application and avoids a
runtime i18n dependency. DOM IDs and request field names remain English because
they are implementation contracts rather than visible prose.

A general translation catalog was considered but rejected because there is no
second locale or locale-selection requirement.

## Risks / Trade-offs

- [A string is missed in a dynamic error path] → add tests that assert Chinese
  presentation text across templates and client scripts.
- [Translation accidentally changes an API literal] → retain existing endpoint
  and payload contract tests in the full regression run.

## Migration Plan

1. Replace presentation strings and add focused localization assertions.
2. Run the page tests and full regression suite.
3. Restart the Flask service to load static assets; rollback is a code revert
   with no data migration.
