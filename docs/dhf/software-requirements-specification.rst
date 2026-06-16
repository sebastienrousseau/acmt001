.. _dhf-software-requirements:

============================================
Software Requirements Specification
============================================

.. list-table:: Document Control
   :widths: 25 75
   :stub-columns: 1

   * - Document ID
     - DHF-003
   * - Version
     - 1.0
   * - Date
     - 2026-03-22
   * - Author
     - acmt001 Engineering
   * - Status
     - Released
   * - ISO 13485 Clause
     - 7.3.3 (Design and Development Outputs)

1. Functional Requirements
--------------------------

1.1 FR-100: XML Generation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 60 25

   * - ID
     - Requirement
     - Priority
   * - FR-101
     - The system shall generate valid ISO 20022 acmt XML messages from
       structured account data using Jinja2 templates.
     - Essential
   * - FR-102
     - The system shall support all 34 published acmt message types
       (acmt.001.001.08 through acmt.037.001.02, including the
       mandate-amendment and account-switching families) via a message-type
       dispatch mechanism (``constants.valid_xml_types``).
     - Essential
   * - FR-103
     - The system shall validate all generated XML against the corresponding
       official XSD schema before returning output.
     - Essential
   * - FR-104
     - The system shall register correct XML namespaces for each acmt message
       type prior to generation.
     - Essential
   * - FR-105
     - The system shall generate unique output file paths to prevent
       overwriting existing files.
     - Important

1.2 FR-200: Data Ingestion
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 60 25

   * - ID
     - Requirement
     - Priority
   * - FR-201
     - The system shall load account data from CSV files via
       ``load_csv_data()``.
     - Essential
   * - FR-202
     - The system shall load account data from JSON files via
       ``load_json_data()``.
     - Essential
   * - FR-203
     - The system shall load account data from JSONL (JSON Lines) files via
       ``load_jsonl_data()``.
     - Essential
   * - FR-204
     - The system shall load account data from SQLite databases via
       ``load_db_data()``.
     - Essential
   * - FR-205
     - The system shall load account data from Apache Parquet files via
       ``load_parquet_data()``.
     - Essential
   * - FR-206
     - The system shall accept account data as Python ``dict`` objects.
     - Essential
   * - FR-207
     - The system shall accept account data as Python ``list`` objects.
     - Essential
   * - FR-208
     - The system shall support streaming ingestion for CSV, JSON, JSONL,
       SQLite, and Parquet sources via ``load_account_data_streaming()`` to
       handle large datasets without loading all data into memory at once.
     - Important

1.3 FR-300: Validation
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 60 25

   * - ID
     - Requirement
     - Priority
   * - FR-301
     - The system shall validate account data against message-type-specific
       JSON schemas via ``SchemaValidator``.
     - Essential
   * - FR-302
     - The system shall validate BIC codes against ISO 9362 format rules via
       ``validate_bic()``.
     - Essential
   * - FR-303
     - The system shall validate IBAN codes using ISO 7064 mod-97-10 checksum
       verification via ``validate_iban()``.
     - Essential
   * - FR-304
     - The system shall validate LEI codes against ISO 17442 format and
       check-digit rules via ``validate_lei()``.
     - Essential
   * - FR-305
     - The system shall validate that all required account fields are present
       before XML generation.
     - Essential
   * - FR-306
     - The system shall provide a ``ValidationService`` with configurable
       validation rules (``ValidationConfig``) and structured
       ``ValidationReport`` output.
     - Important

1.4 FR-400: SWIFT Compliance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 60 25

   * - ID
     - Requirement
     - Priority
   * - FR-401
     - The system shall validate account data fields against the SWIFT
       Z/z character set.
     - Essential
   * - FR-402
     - The system shall enforce SWIFT field length limits for all applicable
       account fields.
     - Essential
   * - FR-403
     - The system shall provide character transliteration for non-SWIFT
       characters where possible.
     - Important
   * - FR-404
     - The system shall generate compliance reports identifying any SWIFT
       standard violations.
     - Important

1.5 FR-500: Message-Type-Specific Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 60 25

   * - ID
     - Requirement
     - Priority
   * - FR-501
     - Account opening messages (acmt.007.001.05, acmt.008.001.05,
       acmt.009.001.04) shall include account-owner identification, account
       servicer BIC, and organisation legal identity (LEI) where the schema
       requires it.
     - Essential
   * - FR-502
     - Account maintenance and mandate-amendment messages (acmt.003.001.08,
       acmt.015.001.05, acmt.016.001.05, acmt.017.001.05, acmt.018.001.05)
       shall include mandate-related information (mandate identifier, mandate
       channel, signature requirements) in generated XML.
     - Essential
   * - FR-503
     - Account closing messages (acmt.019.001.04, acmt.020.001.04,
       acmt.021.001.04) shall include status and reason codes for the
       closing instruction.
     - Essential
   * - FR-504
     - Identification messages (acmt.022.001.04, acmt.023.001.04,
       acmt.024.001.04) shall include verification identifiers and
       verification indicators in generated XML.
     - Essential
   * - FR-505
     - Status report messages (acmt.005.001.06, acmt.006.001.07) shall use
       the assigner/assignee and original-identifier fields for status
       correlation.
     - Essential
   * - FR-506
     - Account-switching messages (acmt.027.001.06 through acmt.037.001.02)
       shall include the switching-lifecycle fields (switch information
       request/response, payment cancellation, redirection, balance transfer
       and acknowledgement, completion notification, payment request/response,
       termination, and technical rejection) in generated XML.
     - Essential

1.6 FR-600: Interfaces
~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 60 25

   * - ID
     - Requirement
     - Priority
   * - FR-601
     - The system shall expose a Python API with ``process_files()`` and
       ``generate_xml_string()`` as public entry points.
     - Essential
   * - FR-602
     - The system shall provide a Click-based CLI with options for message
       type, template, schema, data source, output directory, dry-run mode,
       and verbose logging.
     - Essential
   * - FR-603
     - The system shall provide a FastAPI REST API with endpoints for health
       check (``/api/health``), validation (``/api/validate``), synchronous
       generation (``/api/generate``), and asynchronous generation
       (``/api/generate/async``).
     - Essential
   * - FR-604
     - The REST API shall support async job management with status polling
       (``/api/status/{job_id}``), cancellation (``/api/jobs/{job_id}``),
       and download (``/api/download/{job_id}``).
     - Important

1.7 FR-700: Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 60 25

   * - ID
     - Requirement
     - Priority
   * - FR-701
     - The system shall raise ``AccountValidationError`` (with sub-types
       ``InvalidIBANError``, ``InvalidBICError``, ``InvalidLEIError``,
       ``MissingRequiredFieldError``) for data validation failures.
     - Essential
   * - FR-702
     - The system shall raise ``XMLGenerationError`` for template rendering
       or XSD validation failures.
     - Essential
   * - FR-703
     - The system shall raise ``DataSourceError`` for file-not-found,
       database errors, or unsupported format errors.
     - Essential
   * - FR-704
     - The system shall raise ``ConfigurationError`` for invalid message
       types, missing environment variables, or configuration file errors.
     - Essential

2. Non-Functional Requirements
------------------------------

2.1 NFR-100: Security
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 60 25

   * - ID
     - Requirement
     - Priority
   * - NFR-101
     - The system shall use ``defusedxml`` for all XML parsing to prevent
       XXE (XML External Entity) injection attacks.
     - Essential
   * - NFR-102
     - The system shall validate all file paths via ``validate_path()`` to
       prevent path traversal attacks, restricting access to the current
       working directory, system temp directory, and ``/var/tmp``.
     - Essential
   * - NFR-103
     - The system shall sanitize all user-supplied values before including
       them in log output via ``sanitize_for_log()``.
     - Essential
   * - NFR-104
     - The system shall use ``autoescape=True`` in the Jinja2 template
       environment to prevent template injection.
     - Essential
   * - NFR-105
     - The system shall run under a non-root user (``appuser``) when
       deployed in Docker.
     - Essential

2.2 NFR-200: Quality
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 60 25

   * - ID
     - Requirement
     - Priority
   * - NFR-201
     - The test suite shall achieve >= 99% branch coverage as enforced by
       ``--cov-fail-under=99``.
     - Essential
   * - NFR-202
     - The codebase shall pass ``mypy --strict`` with zero errors.
     - Essential
   * - NFR-203
     - The codebase shall pass ``bandit -r acmt001/`` with zero findings.
     - Essential
   * - NFR-204
     - The codebase shall pass ``ruff check`` and ``black --check`` with
       zero findings.
     - Essential

2.3 NFR-300: Compatibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 60 25

   * - ID
     - Requirement
     - Priority
   * - NFR-301
     - The system shall support Python 3.9, 3.10, 3.11, and 3.12.
     - Essential
   * - NFR-302
     - The system shall pass CI on Linux (Ubuntu), macOS, and Windows.
     - Essential
   * - NFR-303
     - The system shall be installable via ``pip install`` and
       ``poetry install``.
     - Essential

2.4 NFR-400: Performance
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 60 25

   * - ID
     - Requirement
     - Priority
   * - NFR-401
     - XSD schema parsing shall be cached (LRU cache, maxsize=16) to avoid
       redundant parsing on repeated validations.
     - Important
   * - NFR-402
     - Streaming data loaders shall process files in configurable chunk sizes
       (default: 1,000 rows) to bound memory usage.
     - Important
   * - NFR-403
     - The system shall log generation timing (milliseconds) for performance
       monitoring.
     - Desirable

2.5 NFR-500: Maintainability
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 60 25

   * - ID
     - Requirement
     - Priority
   * - NFR-501
     - The codebase shall use structured logging with defined event types
       (``Events`` class) and field names (``Fields`` class).
     - Important
   * - NFR-502
     - All exceptions shall inherit from ``Acmt001Error`` to enable
       catch-all handling and maintain a consistent exception hierarchy.
     - Important
   * - NFR-503
     - The message-type dispatch mechanism shall be extensible via the
       ``xml_data_preparers`` dictionary without modifying existing code.
     - Important
