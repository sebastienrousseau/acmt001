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

"""Acmt001 FastAPI REST API module."""

from acmt001.api import app, job_manager, models
from acmt001.api.job_manager import JobManager, JobStatus
from acmt001.api.models import (
    DataSourceType,
    GenerateXMLRequest,
    GenerateXMLResponse,
    HealthResponse,
    JobStatusResponse,
    MessageType,
    ValidationError,
    ValidationRequest,
    ValidationResponse,
)

__all__ = [
    "app",
    "JobManager",
    "JobStatus",
    "job_manager",
    "models",
    "DataSourceType",
    "GenerateXMLRequest",
    "GenerateXMLResponse",
    "HealthResponse",
    "JobStatusResponse",
    "MessageType",
    "ValidationError",
    "ValidationRequest",
    "ValidationResponse",
]
