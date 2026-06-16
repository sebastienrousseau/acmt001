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

"""Pydantic models for FastAPI request/response validation."""

# pylint: disable=too-few-public-methods

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class DataSourceType(str, Enum):
    """Supported data source types."""

    CSV = "csv"
    SQLITE = "sqlite"
    JSON = "json"
    JSONL = "jsonl"
    PARQUET = "parquet"


class MessageType(str, Enum):
    """Supported ISO 20022 acmt message types."""

    ACMT_001_08 = "acmt.001.001.08"
    ACMT_002_08 = "acmt.002.001.08"
    ACMT_003_08 = "acmt.003.001.08"
    ACMT_005_06 = "acmt.005.001.06"
    ACMT_006_07 = "acmt.006.001.07"
    ACMT_007_05 = "acmt.007.001.05"
    ACMT_008_05 = "acmt.008.001.05"
    ACMT_009_04 = "acmt.009.001.04"
    ACMT_010_04 = "acmt.010.001.04"
    ACMT_011_04 = "acmt.011.001.04"
    ACMT_012_04 = "acmt.012.001.04"
    ACMT_013_04 = "acmt.013.001.04"
    ACMT_014_05 = "acmt.014.001.05"
    ACMT_015_05 = "acmt.015.001.05"
    ACMT_016_05 = "acmt.016.001.05"
    ACMT_017_05 = "acmt.017.001.05"
    ACMT_018_05 = "acmt.018.001.05"
    ACMT_019_04 = "acmt.019.001.04"
    ACMT_020_04 = "acmt.020.001.04"
    ACMT_021_04 = "acmt.021.001.04"
    ACMT_022_04 = "acmt.022.001.04"
    ACMT_023_04 = "acmt.023.001.04"
    ACMT_024_04 = "acmt.024.001.04"
    ACMT_027_06 = "acmt.027.001.06"
    ACMT_028_06 = "acmt.028.001.06"
    ACMT_029_06 = "acmt.029.001.06"
    ACMT_030_04 = "acmt.030.001.04"
    ACMT_031_06 = "acmt.031.001.06"
    ACMT_032_06 = "acmt.032.001.06"
    ACMT_033_02 = "acmt.033.001.02"
    ACMT_034_06 = "acmt.034.001.06"
    ACMT_035_02 = "acmt.035.001.02"
    ACMT_036_01 = "acmt.036.001.01"
    ACMT_037_02 = "acmt.037.001.02"


class ValidationRequest(BaseModel):  # pylint: disable=too-few-public-methods
    """Request model for data validation."""

    data_source: DataSourceType = Field(
        ..., description="Type of data source (csv, sqlite, json, etc.)"
    )
    file_path: str = Field(..., description="Path to the data file")
    message_type: MessageType = Field(
        default=MessageType.ACMT_007_05,
        description="ISO 20022 acmt.007 message type",
    )
    table_name: Optional[str] = Field(
        default=None,
        description="Table name for SQLite sources",
    )

    class Config:
        """Pydantic config."""

        use_enum_values = False


class GenerateXMLRequest(BaseModel):
    """Request model for XML generation."""

    data_source: DataSourceType = Field(..., description="Type of data source")
    file_path: str = Field(..., description="Path to the data file")
    message_type: MessageType = Field(
        default=MessageType.ACMT_007_05,
        description="ISO 20022 acmt.007 message type",
    )
    output_dir: Optional[str] = Field(
        default=None,
        description="Output directory for generated XML",
    )
    validate_only: bool = Field(
        default=False,
        description="Only validate, don't generate XML",
    )
    table_name: Optional[str] = Field(
        default=None,
        description="Table name for SQLite sources",
    )

    class Config:
        """Pydantic config."""

        use_enum_values = False


class ValidationError(BaseModel):
    """Validation error details."""

    field: str = Field(..., description="Field name or JSON path")
    message: str = Field(..., description="Error message")
    value: Optional[Any] = Field(None, description="The invalid value")


class ValidationResponse(BaseModel):
    """Response model for validation results."""

    is_valid: bool = Field(..., description="Whether data is valid")
    total_rows: int = Field(..., description="Total number of rows")
    valid_rows: int = Field(default=0, description="Number of valid rows")
    invalid_rows: int = Field(default=0, description="Number of invalid rows")
    errors: list[ValidationError] = Field(
        default_factory=list,
        description="List of validation errors",
    )

    @field_validator("invalid_rows", mode="after")
    @classmethod
    def calculate_invalid_rows(cls, v: int, info: ValidationInfo) -> int:
        """Calculate invalid rows from total and valid counts.

        Args:
            v: Current invalid_rows value.
            info: Validation info containing all field values.

        Returns:
            Calculated invalid rows (total - valid).
        """
        # Pydantic v2 uses info.data instead of values dict
        if hasattr(info, "data"):
            data = info.data
            if "total_rows" in data and "valid_rows" in data:
                total = int(data["total_rows"])
                valid = int(data["valid_rows"])
                return total - valid
        return v  # pragma: no cover


class GenerateXMLResponse(BaseModel):
    """Response model for XML generation."""

    success: bool = Field(..., description="Whether generation succeeded")
    message: str = Field(..., description="Result message")
    file_path: Optional[str] = Field(None, description="Path to generated XML")
    validation_errors: list[ValidationError] = Field(
        default_factory=list,
        description="Validation errors if validation failed",
    )


class JobStatusResponse(BaseModel):
    """Response model for job status."""

    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(
        ...,
        description="Current job status (pending, processing, success, failed, cancelled)",
    )
    message: str = Field(..., description="Status message")
    result: Optional[GenerateXMLResponse] = Field(
        None, description="Result when status is success"
    )
    error: Optional[str] = Field(None, description="Error message if failed")
    progress_percent: int = Field(
        default=0, description="Progress percentage (0-100)"
    )

    class Config:
        """Pydantic config."""

        use_enum_values = True


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    message: str = Field(..., description="Health check message")


class IdentifierValidationRequest(BaseModel):
    """Request model for financial identifier validation."""

    kind: str = Field(
        ...,
        description="Identifier kind: 'iban', 'bic', or 'lei'",
    )
    value: str = Field(..., description="The identifier value to validate")

    model_config = {
        "json_schema_extra": {
            "example": {"kind": "bic", "value": "NWBKGB2LXXX"}
        }
    }
