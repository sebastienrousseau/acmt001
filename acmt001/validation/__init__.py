# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Validation module for Acmt001.

This module provides centralized validation services for account data,
templates, schemas, and data sources.
"""

from acmt001.validation.bic_validator import (
    validate_bic,
    validate_bic_format,
    validate_bic_safe,
)
from acmt001.validation.iban_validator import (
    validate_iban,
    validate_iban_checksum,
    validate_iban_format,
    validate_iban_safe,
)
from acmt001.validation.lei_validator import (
    validate_lei,
    validate_lei_checksum,
    validate_lei_format,
    validate_lei_safe,
)
from acmt001.validation.service import (
    ValidationConfig,
    ValidationReport,
    ValidationResult,
    ValidationService,
)

__all__ = [
    # Service classes
    "ValidationService",
    "ValidationConfig",
    "ValidationResult",
    "ValidationReport",
    # IBAN validation
    "validate_iban",
    "validate_iban_format",
    "validate_iban_checksum",
    "validate_iban_safe",
    # BIC validation
    "validate_bic",
    "validate_bic_format",
    "validate_bic_safe",
    # LEI validation
    "validate_lei",
    "validate_lei_format",
    "validate_lei_checksum",
    "validate_lei_safe",
]
