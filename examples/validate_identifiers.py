#!/usr/bin/env python3
"""Example: IBAN, BIC, and LEI validation.

Usage:
    python examples/validate_identifiers.py

Demonstrates every public validator variant:
  - validate_*        -> (is_valid, message) tuple; raises Invalid*Error on
                         malformed input
  - validate_*_format -> structural check only
  - validate_*_safe   -> plain bool, never raises
"""

from acmt001.exceptions import InvalidIBANError
from acmt001.validation import (
    validate_bic,
    validate_bic_format,
    validate_bic_safe,
    validate_iban,
    validate_iban_checksum,
    validate_iban_format,
    validate_iban_safe,
    validate_lei,
    validate_lei_format,
    validate_lei_safe,
)

# --- IBAN (ISO 13616 + ISO 7064 mod-97 checksum) ---------------------------
print("IBAN")
print("  validate_iban:        ", validate_iban("GB29NWBK60161331926819"))
print(
    "  validate_iban_format: ", validate_iban_format("GB29NWBK60161331926819")
)
print(
    "  validate_iban_checksum:",
    validate_iban_checksum("GB29NWBK60161331926819"),
)
print("  validate_iban_safe:   ", validate_iban_safe("GB29NWBK60161331926819"))
print("  bad IBAN (safe):      ", validate_iban_safe("GB00NWBK60161331926819"))
try:
    validate_iban("GB00NWBK60161331926819")  # bad check digits
except InvalidIBANError as e:
    print("  bad IBAN raises:      ", type(e).__name__)

# --- BIC (ISO 9362, 8 or 11 characters) ------------------------------------
print("BIC")
print("  validate_bic:         ", validate_bic("NWBKGB2LXXX"))
print("  validate_bic_format:  ", validate_bic_format("NWBKGB2L"))
print("  validate_bic_safe:    ", validate_bic_safe("NWBKGB2LXXX"))
print("  bad BIC (safe):       ", validate_bic_safe("INVALID"))

# --- LEI (ISO 17442, 20 chars with ISO 7064 checksum) ----------------------
print("LEI")
print("  validate_lei:         ", validate_lei("5493001KJTIIGC8Y1R12"))
print("  validate_lei_format:  ", validate_lei_format("5493001KJTIIGC8Y1R12"))
print("  validate_lei_safe:    ", validate_lei_safe("5493001KJTIIGC8Y1R12"))
print("  bad LEI (safe):       ", validate_lei_safe("5493001KJTIIGC8Y1R13"))
