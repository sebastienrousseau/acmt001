# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Model Context Protocol (MCP) server exposing acmt001 as agent tools
  (`acmt001-mcp`, optional `servers` extra, Python 3.10+)
- Language Server Protocol (LSP) server for authoring account-data JSON
  with diagnostics, completion, and hover (`acmt001-lsp`, optional
  `servers` extra, Python 3.10+)
- Shared service facade (`acmt001.services`) backing the CLI, API, MCP,
  and LSP interfaces
- Click-based CLI for batch processing
- IBAN, BIC, and LEI validators
- JSON schema validation for all supported message types
- Path traversal protection and security hardening

[0.0.1]: https://github.com/sebastienrousseau/acmt001/releases/tag/v0.0.1
