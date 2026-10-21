# declarative-skills Specification

## Purpose

Allow teachers and students to use built-in classroom skills and teacher-uploaded declarative skills with explicit, bounded and inspectable execution semantics.

## Requirements

### Requirement: Built-in and uploaded skill catalog
The system SHALL provide at least two built-in skills and allow teachers to upload a UTF-8 .json skill manifest with version=1, name, description, instructions and one to three named prompt steps. The entire file SHALL be at most 16 KiB; fields, sizes and unknown properties SHALL be validated. Skills SHALL be class-scoped, inspectable and deletable by same-class teachers; students SHALL be read-only. Shell, Python, filesystem commands and archive extraction SHALL NOT be executed.

#### Scenario: Upload and use a skill
- **WHEN** a teacher uploads a valid JSON skill
- **THEN** it appears in the class skill selector and can be inspected and selected by a student

#### Scenario: Reject malformed or executable packages
- **WHEN** an invalid, oversized, unsupported-extension or unknown-step-type file is uploaded
- **THEN** the API returns 400 without storing or executing it

### Requirement: Sequential skill execution
A selected skill SHALL send its complete validated manifest in system context on each prompt step. Steps SHALL execute in declared order; each step SHALL receive current user input, the rendered selected template, bounded knowledge if bound, and the previous step result when present. The last step SHALL produce the user-visible final answer; each step's status and output SHALL be recorded. A failed step SHALL stop subsequent steps and expose a failed run rather than a success. Selected external tools SHALL remain bounded and permitted during skill execution.

#### Scenario: Execute a two-step skill
- **WHEN** a user selects the built-in draft-and-review skill
- **THEN** draft and review execute in order, review receives draft output, and both calls contain the full manifest

#### Scenario: Stop on provider failure
- **WHEN** the model fails during a skill step
- **THEN** later steps do not execute and the record shows failure
