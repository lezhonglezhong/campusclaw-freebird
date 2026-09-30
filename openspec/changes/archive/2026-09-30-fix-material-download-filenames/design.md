# Design
Use the server-generated storage path for filesystem safety, but derive the attachment name from Unicode `display_name` plus the stored content suffix when it is absent. Let Flask generate RFC-compatible download headers; do not use `secure_filename` for browser display names.
