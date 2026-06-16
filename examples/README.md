# Acmt001 examples

Runnable, self-contained examples covering every part of the library. Run any
of them from the repository root:

```sh
python examples/<name>.py
```

| Example | Demonstrates |
|---------|--------------|
| [`services_facade.py`](services_facade.py) | The unified `acmt001.services` layer — list types, schema, validate, generate |
| [`generate_xml.py`](generate_xml.py) | Generate a single message with `generate_xml_string` |
| [`all_message_types.py`](all_message_types.py) | Generate **all 34** message types from one record |
| [`data_sources.py`](data_sources.py) | Load CSV, JSON, JSONL, SQLite, and Parquet — plus streaming |
| [`validate_identifiers.py`](validate_identifiers.py) | Every IBAN / BIC / LEI validator variant |
| [`validation_service.py`](validation_service.py) | `ValidationService` pre-flight + `SchemaValidator` |
| [`compliance_cleansing.py`](compliance_cleansing.py) | SWIFT charset validation, transliteration, length enforcement |
| [`account_management.py`](account_management.py) | End-to-end: cleanse → validate → open + close an account |
| [`rest_api_client.py`](rest_api_client.py) | Drive the REST API (health, types, validate, generate, portals) |
| [`mcp_tools.py`](mcp_tools.py) | Call the MCP server's six tools (needs `acmt001-mcp`) |
| [`lsp_helpers.py`](lsp_helpers.py) | The LSP diagnostics / completion / hover helpers (needs `acmt001-lsp`) |

The MCP and LSP examples require their companion packages:

```sh
pip install acmt001-mcp acmt001-lsp   # Python 3.10+
```

Bundled sample data: `accounts.csv`, `accounts.json`, `accounts.jsonl`.
