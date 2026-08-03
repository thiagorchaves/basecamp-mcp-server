# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

### Added

- Preview-bound, short-lived, single-use confirmation tokens for sensitive Card Table writes.
- Dedicated previews for card due-date changes and investigation reports.
- Sanitized architecture diagram for project documentation.
- Tests covering token reuse, payload tampering, and confirmed card updates.

### Changed

- Card update, due-date, and investigation-report MCP tools now require the `confirmation_id` returned by their matching preview tool.
- GitHub Actions `checkout` usage is pinned to an immutable commit SHA.
- Documentation now distinguishes server-enforced preview binding from MCP-host responsibility for actual human approval.

## [0.2.0] - 2026-07-07

### Added

- Public open-source project metadata and MIT license.
- Read-only-by-default tool registration.
- OAuth refresh-token support and local callback state validation.
- Automatic Basecamp pagination through `Link` headers.
- CI, tests, contribution guidance, and security policy.

### Fixed

- Card due-date updates now use the canonical Card Table card endpoint.
- Archived and trashed project filtering now uses the Basecamp API query parameter.
- Removed local virtual environments, bytecode, duplicate scripts, and private paths.
