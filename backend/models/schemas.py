"""
Pydantic Models / Schemas

Defines request/response models for API validation.
"""

import re
from typing import List, Optional
from pydantic import BaseModel, Field, validator


# Valid IEC 61131-3 data types
VALID_DATA_TYPES = {
    "BOOL", "SINT", "INT", "DINT", "LINT", "USINT", "UINT", "UDINT", "ULINT",
    "REAL", "LREAL", "BYTE", "WORD", "DWORD", "LWORD", "STRING", "TIME", "DATE"
}


class NarrativeRequest(BaseModel):
    """Request model for code generation."""
    narrative: str = Field(..., min_length=1, max_length=5000)
    
    @validator('narrative')
    def validate_narrative(cls, v):
        if not v or not v.strip():
            raise ValueError('Narrative cannot be empty')
        return v.strip()


class Variable(BaseModel):
    """Model for a device variable."""
    deviceName: str = Field(..., min_length=1, max_length=100)
    dataType: str = Field(..., min_length=1)
    range: str = Field(default="")
    MetaData: str = Field(default="")
    id: Optional[str] = None
    
    @validator('deviceName')
    def validate_device_name(cls, v):
        v = v.strip()
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', v):
            raise ValueError('Device name must be a valid identifier')
        return v
    
    @validator('dataType')
    def validate_data_type(cls, v):
        upper_v = v.upper()
        if upper_v not in VALID_DATA_TYPES:
            raise ValueError(f'Invalid data type. Must be one of: {", ".join(VALID_DATA_TYPES)}')
        return upper_v


class SaveVariablesRequest(BaseModel):
    """Request model for saving variables."""
    variables: List[Variable]


class GenerateResponse(BaseModel):
    """Response model for code generation."""
    status: str
    code: Optional[str] = None
    message: Optional[str] = None


class StatusResponse(BaseModel):
    """Generic status response."""
    status: str
    message: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    message: str
    database_connected: bool
