# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.9] - 2026-08-29

Aligns the `acmt001` suite on one version number, and adds the two gates
that were missing: a benchmark and a scheduled drift check.

### Added

- `benches/bench_generate_xml.py` measures what an acmt message costs to
  build. It reports output size beside the timings because the two are
  easy to confuse: handing many rows to a single-account message type
  makes the per-row cost fall while the output stays one message, which
  reads as a batching win and is the opposite.
- `scripts/check_suite_consistency.py` and a scheduled `Suite
  Consistency` workflow compare this tree, and every published member of
  the suite, against PyPI. A member left a release behind still installs
  and still passes its own tests; only the index disagrees, and only if
  somebody looks.
- `tests/test_suite_conformance.py`, the shared suite conformance gate.
- `SECURITY.md`, which the conformance gate requires and this repository
  did not ship.

### Changed

- Version aligned to `0.0.9` across `acmt001`, `acmt001-lsp` and
  `acmt001-mcp`. These three ship as one suite and had drifted to
  `0.0.5`, `0.0.2` and `0.0.8` respectively.

## [0.0.5] - 2026-08-28

### Changed

- **`xmlschema` moves to `>=4.3.2,<5.0.0`,** from `>=3.4.0 <4.0.0`.

  The cap was the last thing in the suite holding xmlschema at 3.
  `pain001` and `camt053` are both on 4, so `iso20022-mcp[all]` — which
  installs this package alongside them — could not resolve at all: pip
  reported `ResolutionImpossible` rather than anything that named the
  cause.

  No source change was needed. This package touches exactly two names
  from the library, `xmlschema.XMLSchema` and
  `xmlschema.XMLSchemaException`, and both are unchanged across the
  major. The full suite passes on 4.3.2 (1020 tests, 99.89% coverage).

- **`constants.VERSION` and `__version__` are no longer asserted against
  a hand-edited literal.** Two tests pinned the string `"0.0.4"`, so
  every release failed them until someone edited the number — churn that
  checked nothing, because `test_package_version.py` already ties all
  five restatements of the version together. They now compare against
  the package and against the semver shape.

### Added

- A floor test for the `xmlschema` constraint, mirroring the
  `cryptography` one. An upper cap that excludes the version a sibling
  package requires is invisible until a dependent tries to install both,
  and then it surfaces as an unexplained resolver failure.

## [0.0.4] - 2026-08-18

### Fixed

- `cryptography` is now `>=48.0.1,<51.0.0`. The published `0.0.3` caps it
  at `<50.0.0`, which makes `cryptography 50.0.0` — the release that
  patches a high-severity advisory — unresolvable for this package and
  everything that depends on it. `acmt001-mcp` inherits that ceiling and
  cannot take the patched version while it stands.

  The cap was precautionary rather than load-bearing: the full suite
  passes unchanged on 50.0.0 (1015 tests, 99.89% coverage).

### Added

- `tests/test_package_version.py`, pinning `__version__` to
  `pyproject.toml`, `constants.VERSION` and the newest `CHANGELOG.md`
  heading, and asserting the `cryptography` constraint actually admits
  50.0.0. Five files restate the version independently and nothing tied
  them together.

## [0.0.3] - 2026-07-16

The **co-install** cut. Relaxes the exact pins that prevented the ISO 20022
MCP suite (`iso20022-mcp[all]`) from resolving alongside camt053, pacs008,
and pain001. No API or functional changes.

### Changed

- **click** relaxed from `==8.1.7` to `>=8.1,<9` (camt053 requires a newer
  click; pain001/pacs008 already accept `>=8.1,<9`).
- **rich** relaxed from `==13.7.1` to `>=13.7.1,<16` (matches camt053;
  pacs008 currently caps the suite at `<14`).
- **markupsafe** relaxed from `==2.1.5` to `>=2.1.5,<4` (camt053 resolves
  markupsafe 3.x; pacs008 caps `<3.0` - the range spans both).

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
