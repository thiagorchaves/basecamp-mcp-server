# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

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
