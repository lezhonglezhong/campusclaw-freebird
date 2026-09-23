# Proposal

## Why

CampusClaw's browser pages are intended for Chinese-speaking course users, but
their visible labels, actions, and error messages are currently English. A
consistent Simplified Chinese interface will make the demonstrated login and
material workflows understandable without changing their authorization or API
behavior.

## What Changes

- Translate all visible login and material-workspace text, including titles,
  form labels, buttons, empty/loading/error/success messages, and dynamic
  material-detail labels, into Simplified Chinese.
- Retain non-visible identifiers, API paths, payload fields, storage behavior,
  session behavior, roles, and authorization decisions unchanged.

## Capabilities

### New Capabilities
- `chinese-browser-localization`: Simplified Chinese presentation of existing
  browser login and material-management flows.

### Modified Capabilities
- None.

## Impact

- Affects only Flask HTML templates, static JavaScript presentation strings,
  and presentation-oriented browser page tests.
- Adds no dependencies, routes, API changes, roles, or data migration.
