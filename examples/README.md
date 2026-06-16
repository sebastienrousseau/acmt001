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

The MCP and LSP servers are separate packages in the acmt001 suite — their
examples live in their own repositories:
[acmt001-mcp](https://github.com/sebastienrousseau/acmt001-mcp) ·
[acmt001-lsp](https://github.com/sebastienrousseau/acmt001-lsp).

Bundled sample data: `accounts.csv`, `accounts.json`, `accounts.jsonl`.
