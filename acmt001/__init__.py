"""The Python acmt001 module."""

__version__ = "0.0.1"

from acmt001.__main__ import main
from acmt001.core.core import process_files
from acmt001.exceptions import AccountValidationError, DataSourceError
from acmt001.xml.generate_xml import generate_xml_string

__all__ = [
    "main",
    "process_files",
    "generate_xml_string",
    "AccountValidationError",
    "DataSourceError",
    "__version__",
]
