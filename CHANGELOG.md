# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 2026-07-11

The **security** cut. Raises the minimum versions of three dependencies to
non-vulnerable releases so the library (and its downstream companions such as
`acmt001-mcp`) resolve patched transitive dependencies. No API or functional
changes; the full test suite (1015 tests, 99.89% coverage) passes unchanged.

### Security

- **cryptography** bumped from `>=44.0.1,<47.0.0` to `>=48.0.1,<50.0.0`
  (resolves the vulnerable-OpenSSL-in-wheels advisory; not imported directly
  by acmt001).
- **pyarrow** bumped from `>=18.0.0,<19.0.0` to `>=23.0.1,<26.0.0`
  (resolves the IPC pre-buffering use-after-free advisory; used only by the
  optional Parquet loader, verified against pyarrow 25).
- **pygments** unpinned from the exact `2.18.0` to `>=2.20.0,<3.0.0`
  (resolves the GUID-matching ReDoS advisory; transitive via `rich`).

## [0.0.1] - 2026-06-16

### Added

- Initial release of the acmt001 library for ISO 20022 acmt Account
  Management messages (account opening, maintenance, closing,
  identification, and switching)
- Support for all 34 ISO 20022 acmt message types (acmt.001 through
  acmt.037), including Account Opening Request (acmt.007.001.05),
  Account Closing Request (acmt.019.001.04), the mandate-amendment
  messages (acmt.016.001.05, acmt.018.001.05), and the full
  account-switching suite (acmt.027.001.06 through acmt.037.001.02)
- Multi-source data ingestion: CSV, JSON, JSONL, SQLite, Parquet
- Jinja2-based XML template engine with XSD validation
- SWIFT compliance module: charset validation, field length enforcement,
  transliteration, and silent rejection prevention
- FastAPI REST API with async job management, message-type and
  identifier endpoints, and an interactive developer portal (Scalar,
  Swagger UI, ReDoc)
- Companion package `acmt001-mcp`: a Model Context Protocol server
  exposing acmt001 as agent tools (Python 3.10+)
- Companion package `acmt001-lsp`: a Language Server for authoring
  account-data JSON with diagnostics, completion, and hover (Python 3.10+)
- Shared service facade (`acmt001.services`) backing the CLI, API, MCP,
  and LSP interfaces
- Click-based CLI for batch processing
- IBAN, BIC, and LEI validators
- JSON schema validation for all supported message types
- Path traversal protection and security hardening

[0.0.1]: https://github.com/sebastienrousseau/acmt001/releases/tag/v0.0.1
