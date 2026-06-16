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

# Validate the CSV data before processing it. The CSV data must contain
# the following columns:
#
# - msg_id (str) - message identifier
# - creation_date_time (datetime) - creation date and time
# - process_id (str) - process identifier
# - account_id (str) - account identifier (IBAN or proprietary)
# - account_currency (str) - account currency (ISO 4217)
# - account_name (str) - account name
# - account_type_cd (str) - account type code
# - account_servicer_bic (str) - account servicer BICFI
# - account_owner_name (str) - account owner name
# - account_owner_country (str) - account owner country code
# - org_full_legal_name (str) - organisation full legal name
# - org_id_lei (str) - organisation LEI


from datetime import datetime
from typing import Any


def _validate_datetime(value: str) -> bool:
    """Validate datetime field.

    Args:
        value: The datetime string to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    # Handle the "Z" suffix for UTC
    cleaned_value = value
    if value.endswith("Z"):
        cleaned_value = value[:-1] + "+00:00"
    try:
        datetime.fromisoformat(cleaned_value)
        return True
    except ValueError:
        try:
            datetime.strptime(cleaned_value, "%Y-%m-%d")
            return True
        except ValueError:
            return False


def _validate_field_type(value: str, data_type: type) -> bool:
    """Validate a single field against its expected type.

    Args:
        value: The field value to validate.
        data_type: The expected data type.

    Returns:
        bool: True if valid, False otherwise.
    """
    try:
        if data_type is int:
            int(value)
        elif data_type is float:
            float(value)
        elif data_type is bool:
            if value.lower() not in ("true", "false"):
                return False
        elif data_type is datetime:
            return _validate_datetime(value)
        # str type always passes if not empty
        return True
    except ValueError:
        return False


def _validate_row(
    row: dict[str, Any], required_columns: dict[str, type]
) -> tuple[list[str], list[str]]:
    """Validate a single row of CSV data.

    Args:
        row: A dictionary containing row data.
        required_columns: Dictionary of required column names and types.

    Returns:
        tuple: (missing_columns, invalid_columns)
    """
    missing_columns = []
    invalid_columns = []

    for column, data_type in required_columns.items():
        raw_value = row.get(column)

        # Single strip operation, cached result
        if raw_value is None:
            missing_columns.append(column)
            continue

        value = raw_value.strip()

        if not value:
            missing_columns.append(column)
            continue

        # Validate type
        if not _validate_field_type(value, data_type):
            invalid_columns.append(column)

    return missing_columns, invalid_columns


def _format_errors(
    row: dict[str, Any],
    missing_columns: list[str],
    invalid_columns: list[str],
    required_columns: dict[str, type],
) -> list[str]:
    """Format error messages for a row.

    Args:
        row: The row with errors.
        missing_columns: List of missing column names.
        invalid_columns: List of invalid column names.
        required_columns: Dictionary of required column types.

    Returns:
        list: List of formatted error messages.
    """
    errors = []
    if missing_columns:
        errors.append(
            f"Error: Missing value(s) for column(s) {missing_columns} in row: {row}"
        )
    if invalid_columns:
        expected_types = [
            required_columns[col].__name__ for col in invalid_columns
        ]
        errors.append(
            f"Error: Invalid data type for column(s) "
            f"{invalid_columns}, expected {expected_types} in row: {row}"
        )
    return errors


def validate_csv_data(data: list[dict[str, Any]]) -> bool:
    """Validate the CSV data before processing it.

    Args:
        data (list): A list of dictionaries containing the CSV data.

    Returns:
        bool: True if the data is valid, False otherwise.
    """
    required_columns = {
        "msg_id": str,
        "creation_date_time": datetime,
        "process_id": str,
        "account_id": str,
        "account_currency": str,
        "account_name": str,
        "account_type_cd": str,
        "account_servicer_bic": str,
        "account_owner_name": str,
        "account_owner_country": str,
        "org_full_legal_name": str,
        "org_id_lei": str,
    }

    if not data:
        print("Error: The CSV data is empty.")
        return False

    is_valid = True
    all_errors = []  # Batch error messages for better performance

    for row in data:
        missing_columns, invalid_columns = _validate_row(row, required_columns)

        if missing_columns or invalid_columns:
            is_valid = False
            all_errors.extend(
                _format_errors(
                    row, missing_columns, invalid_columns, required_columns
                )
            )

    # Single print operation for all errors
    if all_errors:
        print("\n".join(all_errors))

    return is_valid
