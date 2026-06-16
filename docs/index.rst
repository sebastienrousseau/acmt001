acmt001 Documentation
=====================

**acmt001** is a Python library for generating ISO 20022 acmt Account
Management XML messages (account opening, maintenance, closing,
identification, and switching). It supports all 34 acmt message types
(acmt.001.001.08 through acmt.037.001.02).

Interfaces
----------

Four developer-facing surfaces sit on top of one shared service layer
(``acmt001.services``), so they all behave identically:

* **Python API** — ``generate_xml_string`` / ``process_files`` /
  ``acmt001.services`` (programmatic generation and validation).
* **Command-line interface** — the ``acmt001`` console command for batch
  generation from CSV, JSON, JSONL, SQLite, or Parquet data.
* **REST API** — a FastAPI application (``acmt001.api.app:app``) with an
  interactive developer portal at ``/``, a Scalar API reference at
  ``/api/reference``, Swagger UI at ``/api/docs``, and ReDoc at
  ``/api/redoc``.
* **MCP server** — a Model Context Protocol server (``acmt001-mcp``) exposing
  the library as tools for AI agents.
* **LSP server** — a Language Server (``acmt001-lsp``) providing diagnostics,
  completion, and hover for account-data JSON files in editors.

The MCP and LSP servers are an optional extra (Python 3.10+):

.. code-block:: sh

   pip install "acmt001[servers]"

Runnable, self-contained examples for every feature live in the ``examples/``
directory (see ``examples/README.md``).

Quick Start
-----------

.. code-block:: python

   from acmt001 import generate_xml_string

   data = [{
       "msg_id": "MSG-001",
       "creation_date_time": "2026-01-15T10:30:00",
       "process_id": "PROC-001",
       "account_id": "GB29NWBK60161331926819",
       "account_currency": "EUR",
       "account_name": "Acme Corp Operating Account",
       "account_type_cd": "CACC",
       "account_servicer_bic": "DEUTDEFF",
       "account_owner_name": "Acme Corp",
       "account_owner_country": "DE",
       "org_full_legal_name": "Acme Corporation GmbH",
       "org_id_lei": "529900T8BM49AURSDO55",
   }]

   xml = generate_xml_string(
       data,
       "acmt.007.001.05",
       "acmt001/templates/acmt.007.001.05/template.xml",
       "acmt001/templates/acmt.007.001.05/acmt.007.001.05.xsd",
   )
   print(xml)

Design History File
-------------------

.. toctree::
   :maxdepth: 2
   :caption: Design History File (DHF)

   dhf/index

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
