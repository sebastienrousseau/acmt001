"""Shared constants and configuration for the acmt001 library."""

import os
from pathlib import Path

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__))).resolve()

VERSION = "0.0.1"
SCHEMAS_DIR = BASE_DIR / "schemas"
TEMPLATES_DIR = BASE_DIR / "templates"

valid_xml_types = [
    "acmt.001.001.08",
    "acmt.002.001.08",
    "acmt.003.001.08",
    "acmt.005.001.06",
    "acmt.006.001.07",
    "acmt.007.001.05",
    "acmt.008.001.05",
    "acmt.009.001.04",
    "acmt.010.001.04",
    "acmt.011.001.04",
    "acmt.012.001.04",
    "acmt.013.001.04",
    "acmt.014.001.05",
    "acmt.015.001.05",
    "acmt.017.001.05",
    "acmt.019.001.04",
    "acmt.020.001.04",
    "acmt.021.001.04",
    "acmt.022.001.04",
    "acmt.023.001.04",
    "acmt.024.001.04",
]

# Human-readable name for every supported ISO 20022 Account Management message.
message_names = {
    "acmt.001.001.08": "Account Opening Instruction",
    "acmt.002.001.08": "Account Details Confirmation",
    "acmt.003.001.08": "Account Modification Instruction",
    "acmt.005.001.06": "Request For Account Management Status Report",
    "acmt.006.001.07": "Account Management Status Report",
    "acmt.007.001.05": "Account Opening Request",
    "acmt.008.001.05": "Account Opening Amendment Request",
    "acmt.009.001.04": "Account Opening Additional Information Request",
    "acmt.010.001.04": "Account Request Acknowledgement",
    "acmt.011.001.04": "Account Request Rejection",
    "acmt.012.001.04": "Account Additional Information Request",
    "acmt.013.001.04": "Account Report Request",
    "acmt.014.001.05": "Account Report",
    "acmt.015.001.05": "Account Excluded Mandate Maintenance Request",
    "acmt.017.001.05": "Account Mandate Maintenance Request",
    "acmt.019.001.04": "Account Closing Request",
    "acmt.020.001.04": "Account Closing Amendment Request",
    "acmt.021.001.04": "Account Closing Additional Information Request",
    "acmt.022.001.04": "Identification Modification Advice",
    "acmt.023.001.04": "Identification Verification Request",
    "acmt.024.001.04": "Identification Verification Report",
}

APP_NAME = "Acmt001"
APP_DESCRIPTION = """
A powerful Python library that enables you to create
ISO 20022 acmt Account Management XML messages (account
opening, maintenance, and closing) from CSV or SQLite
data files.\n
https://acmt001.com
"""

__all__ = [
    "APP_DESCRIPTION",
    "APP_NAME",
    "BASE_DIR",
    "SCHEMAS_DIR",
    "TEMPLATES_DIR",
    "VERSION",
    "message_names",
    "valid_xml_types",
]
