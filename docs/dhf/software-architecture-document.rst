.. _dhf-software-architecture:

============================================
Software Architecture Document
============================================

.. list-table:: Document Control
   :widths: 25 75
   :stub-columns: 1

   * - Document ID
     - DHF-004
   * - Version
     - 1.0
   * - Date
     - 2026-03-22
   * - Author
     - acmt001 Engineering
   * - Status
     - Released
   * - ISO 13485 Clause
     - 7.3.4 (Design and Development Review)

1. Module Architecture
----------------------

The acmt001 library is organized into 14 packages, each with a single
responsibility:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Package
     - Responsibility
   * - ``api/``
     - FastAPI REST API application (``app.py``), async job management
       (``job_manager.py``), Pydantic request/response models (``models.py``)
   * - ``cli/``
     - Click-based command-line interface (``cli.py``) with options for message
       type, template, schema, data, output directory, dry-run, and verbose
   * - ``compliance/``
     - SWIFT compliance: charset validation (Z/z set), field length
       enforcement, transliteration (``swift_charset.py``)
   * - ``context/``
     - Application context singleton for logger configuration
       (``context.py``)
   * - ``core/``
     - Main orchestration: ``process_files()``, ``_load_data()``,
       ``_generate_and_log()``, ``_validate_inputs()``,
       ``_determine_data_source_type()`` (``core.py``)
   * - ``csv/``
     - CSV data loading (``load_csv_data.py``) and validation
       (``validate_csv_data.py``), including streaming variant
   * - ``data/``
     - Universal data loader dispatch: ``load_account_data()`` routes to
       format-specific loaders (``loader.py``)
   * - ``db/``
     - SQLite loading (``load_db_data.py``), streaming variant
       (``load_db_data_streaming.py``), input validation
       (``validate_db_data.py``)
   * - ``json/``
     - JSON and JSONL loading with streaming support
       (``load_json_data.py``)
   * - ``parquet/``
     - Apache Parquet loading with streaming support
       (``load_parquet_data.py``)
   * - ``security/``
     - Path traversal protection (``validate_path()``), log sanitization
       (``sanitize_for_log()``), ``PathValidationError``, ``SecurityError``
       (``path_validator.py``)
   * - ``validation/``
     - BIC validation (``bic_validator.py``), IBAN validation
       (``iban_validator.py``), LEI validation (``lei_validator.py``), JSON
       schema validation (``schema_validator.py``), ``ValidationService`` with
       configurable rules (``service.py``)
   * - ``xml/``
     - XML generation (``generate_xml.py``), XSD validation
       (``validate_via_xsd.py``), namespace registration
       (``register_namespaces.py``), file I/O (``write_xml_to_file.py``,
       ``xml_to_string.py``, ``generate_updated_xml_file_path.py``)
   * - ``templates/``
     - 34 message-type directories, each containing a Jinja2 template
       (``template.xml``), XSD schema (``.xsd``), and sample output (``.xml``)

Top-level modules:

- ``__init__.py`` — Public API exports (``process_files``,
  ``generate_xml_string``, ``AccountValidationError``, ``DataSourceError``,
  ``__version__``)
- ``__main__.py`` — ``main()`` entry point for ``python -m acmt001``
- ``constants.py`` — ``valid_xml_types`` list, ``message_names`` map,
  ``BASE_DIR``, ``SCHEMAS_DIR``, ``TEMPLATES_DIR``
- ``exceptions.py`` — Exception hierarchy
- ``logging_schema.py`` — Structured logging (``Events``, ``Fields``,
  ``log_event()``)

2. Data Flow
------------

The primary data flow through the system follows this path::

    User Input
        │
        ▼
    process_files(xml_message_type, template, schema, data_source)
        │
        ├─▶ _validate_inputs()          # Check message type + file paths
        │
        ├─▶ _determine_data_source_type()  # Detect format from extension/type
        │
        ├─▶ _load_data()
        │       │
        │       └─▶ load_account_data()  # Universal dispatcher
        │               │
        │               ├─▶ load_csv_data()      # .csv
        │               ├─▶ load_json_data()     # .json
        │               ├─▶ load_jsonl_data()    # .jsonl
        │               ├─▶ load_db_data()       # .db
        │               ├─▶ load_parquet_data()  # .parquet
        │               └─▶ pass-through         # list/dict
        │
        ├─▶ register_namespaces()       # Message-type-specific XML namespaces
        │
        └─▶ _generate_and_log()
                │
                └─▶ generate_xml_string(data, message_type, template, schema)
                        │
                        ├─▶ validate_path()              # Path jail check
                        ├─▶ _XML_DATA_PREPARERS[type]()   # Message-type dispatch
                        ├─▶ Environment(autoescape=True)  # Jinja2 rendering
                        ├─▶ template.render(**data)       # XML string output
                        └─▶ validate_xml_string_via_xsd() # XSD validation
                                │
                                └─▶ defusedxml.ElementTree  # Safe XML parsing
                                        │
                                        └─▶ Validated XML string returned

3. Message-Type Dispatch Strategy
---------------------------------

Message-type-specific XML generation is handled through a dispatch dictionary
in ``acmt001/xml/generate_xml.py``:

.. code-block:: python

   _XML_DATA_PREPARERS = {
       "acmt.001.001.08": _prepare_account_opening,
       "acmt.002.001.08": _prepare_account_modification,
       "acmt.003.001.08": _prepare_account_modification,
       "acmt.005.001.06": _prepare_account_status,
       "acmt.006.001.07": _prepare_account_status,
       "acmt.007.001.05": _prepare_account_opening,
       "acmt.008.001.05": _prepare_account_amendment,
       "acmt.009.001.04": _prepare_account_additional_info,
       "acmt.010.001.04": _prepare_account_response,
       "acmt.011.001.04": _prepare_account_response,
       "acmt.012.001.04": _prepare_account_additional_info,
       "acmt.013.001.04": _prepare_account_report,
       "acmt.014.001.05": _prepare_account_report,
       "acmt.015.001.05": _prepare_account_maintenance,
       "acmt.016.001.05": _prepare_account_maintenance,
       "acmt.017.001.05": _prepare_account_maintenance,
       "acmt.018.001.05": _prepare_account_maintenance,
       "acmt.019.001.04": _prepare_account_closing,
       "acmt.020.001.04": _prepare_account_amendment,
       "acmt.021.001.04": _prepare_account_additional_info,
       "acmt.022.001.04": _prepare_identification,
       "acmt.023.001.04": _prepare_identification,
       "acmt.024.001.04": _prepare_identification,
       "acmt.027.001.06": _prepare_account_switch,
       "acmt.028.001.06": _prepare_account_switch,
       "acmt.029.001.06": _prepare_account_switch,
       "acmt.030.001.04": _prepare_account_switch,
       "acmt.031.001.06": _prepare_account_switch,
       "acmt.032.001.06": _prepare_account_switch,
       "acmt.033.001.02": _prepare_account_switch,
       "acmt.034.001.06": _prepare_account_switch,
       "acmt.035.001.02": _prepare_account_switch,
       "acmt.036.001.01": _prepare_account_switch,
       "acmt.037.001.02": _prepare_account_switch,
   }

**Preparer groupings and their distinguishing features:**

.. list-table::
   :header-rows: 1
   :widths: 28 32 40

   * - Preparer
     - Message Types
     - Distinguishing Features
   * - ``_prepare_account_opening``
     - acmt.001, acmt.007
     - Account-owner identity, account servicer BIC, organisation LEI
   * - ``_prepare_account_modification``
     - acmt.002, acmt.003
     - Account detail confirmation and modification fields
   * - ``_prepare_account_status``
     - acmt.005, acmt.006
     - Assigner/assignee, original identifier, status/reason correlation
   * - ``_prepare_account_amendment``
     - acmt.008, acmt.020
     - Amendment of opening/closing instructions
   * - ``_prepare_account_additional_info``
     - acmt.009, acmt.012, acmt.021
     - Additional-information request fields
   * - ``_prepare_account_response``
     - acmt.010, acmt.011
     - Acknowledgement and rejection status/reason codes
   * - ``_prepare_account_report``
     - acmt.013, acmt.014
     - Account report request and report content
   * - ``_prepare_account_maintenance``
     - acmt.015, acmt.016, acmt.017, acmt.018
     - Mandate maintenance and amendment information (mandate id, channel,
       signatures)
   * - ``_prepare_account_closing``
     - acmt.019
     - Closing instruction status and reason codes
   * - ``_prepare_identification``
     - acmt.022, acmt.023, acmt.024
     - Verification identifier and verification indicator
   * - ``_prepare_account_switch``
     - acmt.027 – acmt.037
     - Account-switching lifecycle fields (switch information, payment
       cancellation, redirection, balance transfer, completion notification,
       payment request/response, termination, technical rejection)

Adding support for future acmt message types requires only:

1. Adding a new message-type Jinja2 template and XSD schema in
   ``templates/``
2. Implementing a data preparer function (or reusing an existing one)
3. Adding an entry to the ``_XML_DATA_PREPARERS`` dictionary
4. Adding the message-type string to ``valid_xml_types`` in ``constants.py``

4. Exception Hierarchy
----------------------

::

    Acmt001Error (base)
    ├── AccountValidationError
    │   ├── InvalidIBANError
    │   │       (fields: message, iban, field, reason)
    │   ├── InvalidBICError
    │   │       (fields: message, bic, field, reason)
    │   ├── InvalidLEIError
    │   │       (fields: message, lei, field, reason)
    │   └── MissingRequiredFieldError
    │           (fields: message, field, row_number, required_fields)
    ├── XMLGenerationError
    │       (Jinja2 rendering failures, XSD validation failures)
    ├── ConfigurationError
    │       (invalid message types, missing env vars, config file errors)
    ├── DataSourceError
    │       (file not found, DB errors, unsupported formats)
    └── SchemaValidationError (alias: XSDValidationError)
            (fields: message, errors: list)

All exceptions inherit from ``Acmt001Error`` to enable catch-all handling at
API and CLI boundaries.

5. Security Architecture
------------------------

5.1 XML External Entity (XXE) Prevention
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Module:** ``acmt001/xml/validate_via_xsd.py``
- **Control:** All XML parsing uses ``defusedxml.ElementTree`` instead of the
  standard library's ``xml.etree.ElementTree``
- **Protection:** Prevents XML bombs, entity expansion attacks, and external
  entity injection
- **Requirement:** NFR-101

5.2 Path Traversal Protection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Module:** ``acmt001/security/path_validator.py``
- **Control:** ``validate_path(untrusted_path, must_exist, base_dir)``
  resolves paths with ``os.path.realpath()`` and rejects any path containing
  ``..`` or resolving outside allowed directories
- **Allowed directories:** current working directory, ``tempfile.gettempdir()``,
  ``/var/tmp`` (Unix only)
- **Requirement:** NFR-102

5.3 SQL Input Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Module:** ``acmt001/db/load_db_data.py``,
  ``acmt001/db/load_db_data_streaming.py``
- **Control:** Table name validation with regex pattern matching; parameterized
  queries where applicable
- **Requirement:** NFR-102

5.4 Log Sanitization
~~~~~~~~~~~~~~~~~~~~~~

- **Module:** ``acmt001/security/path_validator.py``,
  ``acmt001/logging_schema.py``
- **Control:** ``sanitize_for_log(user_input, max_length=100)`` strips control
  characters and truncates input before log emission; automatic PII redaction
  for IBAN, BIC, LEI, and account-owner names
- **Requirement:** NFR-103

5.5 Template Injection Prevention
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Module:** ``acmt001/xml/generate_xml.py``
- **Control:** ``Environment(loader=FileSystemLoader(...), autoescape=True)``
- **Protection:** All template variables are auto-escaped, preventing server-side
  template injection (SSTI)
- **Requirement:** NFR-104

5.6 Container Security
~~~~~~~~~~~~~~~~~~~~~~~~

- **Module:** ``Dockerfile``
- **Control:** Application runs as ``appuser`` (non-root), slim base image,
  health check endpoint
- **Requirement:** NFR-105

6. Interface Specifications
---------------------------

6.1 Python API
~~~~~~~~~~~~~~~

.. code-block:: python

   # Primary entry point — full pipeline
   process_files(
       xml_message_type: str,          # e.g. "acmt.007.001.05"
       xml_template_file_path: str,    # path to Jinja2 template
       xsd_schema_file_path: str,      # path to XSD schema
       data_file_path: Union[str, list, dict],  # data source
   ) -> None

   # Low-level — returns XML string without file I/O
   generate_xml_string(
       data: Union[list, dict],
       account_management_message_type: str,
       xml_template_path: str,
       xsd_schema_path: str,
   ) -> str

6.2 CLI
~~~~~~~~

::

   acmt001 -t <message-type> -m <template> -s <schema> -d <data>
           [-o <output-dir>] [--dry-run] [-v]

**Exit codes:** 0 (success), 1 (validation/processing error), 2 (invalid arguments)

6.3 REST API
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 10 30 60

   * - Method
     - Endpoint
     - Purpose
   * - GET
     - ``/api/health``
     - Health check
   * - POST
     - ``/api/validate``
     - Validate account data without generating XML
   * - POST
     - ``/api/generate``
     - Generate XML synchronously
   * - POST
     - ``/api/generate/async``
     - Submit async XML generation job
   * - GET
     - ``/api/status/{job_id}``
     - Poll async job status
   * - DELETE
     - ``/api/jobs/{job_id}``
     - Cancel async job
   * - GET
     - ``/api/download/{job_id}``
     - Download generated XML from completed job

7. Design Decisions and Rationale
---------------------------------

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Decision
     - Choice
     - Rationale
   * - Template engine
     - Jinja2
     - Mature, well-documented, supports autoescape; separates XML structure
       from data logic
   * - XML parser
     - defusedxml
     - Drop-in replacement for stdlib with XXE protection; no API changes
       required
   * - Message-type dispatch
     - Dictionary of functions
     - O(1) lookup, extensible without modifying existing code, each
       message-type group is isolated
   * - Validation library
     - xmlschema + jsonschema
     - Official XSD/JSON Schema implementations; comprehensive error reporting
   * - CLI framework
     - Click
     - Declarative option/argument syntax, automatic help text, composable
       commands
   * - REST framework
     - FastAPI
     - Async support, automatic OpenAPI docs, Pydantic validation, type hints
   * - Data formats
     - CSV, JSON, JSONL, SQLite, Parquet
     - Covers spreadsheet exports (CSV), API responses (JSON/JSONL), databases
       (SQLite), and analytics pipelines (Parquet)
   * - Streaming support
     - Chunked iterators
     - Bounds memory usage for large datasets; configurable chunk size
   * - Exception hierarchy
     - Single base class
     - Enables catch-all at boundaries while preserving specific error context
   * - Path security
     - Allowlist directories
     - Defense-in-depth; even if application logic is wrong, path jail prevents
       traversal
