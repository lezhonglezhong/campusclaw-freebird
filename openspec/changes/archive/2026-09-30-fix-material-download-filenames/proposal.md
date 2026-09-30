# Proposal
## Why
Downloaded Chinese material names are stripped by filename sanitization and may lose their extension.
## What Changes
- Preserve Unicode display names in download responses and append the stored material suffix when absent.
## Capabilities
### Modified Capabilities
- `class-scoped-material-access`: Download presentation filename and MIME type.
## Non-Goals
- Changing authorization, storage paths, or upload formats.
