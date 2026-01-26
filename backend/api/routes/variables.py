"""
Variables Routes

API endpoints for variable management.
"""

import json
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File

from ...models import SaveVariablesRequest, StatusResponse
from ...services import variables_service, VariablesServiceError
from ...core import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/variables", tags=["Variables"])


@router.get("", response_model=dict)
@router.get("/", response_model=dict)
def get_variables():
    """Get all variables from the database."""
    try:
        variables = variables_service.get_all()
        return {"status": "ok", "variables": variables}
        
    except VariablesServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error getting variables: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve variables")


@router.post("", response_model=StatusResponse)
@router.post("/", response_model=StatusResponse)
def save_variables(body: SaveVariablesRequest):
    """
    Synchronize variables with the database.
    Deletes removed items, updates existing, and adds new ones.
    """
    try:
        result = variables_service.save_all(body.variables)
        return StatusResponse(**result)
        
    except VariablesServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error saving variables: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save variables")


@router.post("/upload", response_model=StatusResponse)
async def upload_variables_json(file: UploadFile = File(...)):
    """Upload variables from a JSON file."""
    # Validate file type
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are allowed")
    
    # Read and check size
    contents = await file.read()
    if len(contents) > settings.max_upload_size:
        max_mb = settings.max_upload_size // 1024 // 1024
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {max_mb}MB")
    
    # Parse JSON
    try:
        variables_list = json.loads(contents.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file format")
    
    # Validate format
    if not isinstance(variables_list, list):
        raise HTTPException(status_code=400, detail="JSON must be an array of variables")
    
    for i, var in enumerate(variables_list):
        if not isinstance(var, dict):
            raise HTTPException(status_code=400, detail=f"Item {i} is not a valid object")
        if 'deviceName' not in var or 'dataType' not in var:
            raise HTTPException(status_code=400, detail=f"Item {i} missing required fields")
    
    # Upload
    try:
        result = variables_service.upload_from_list(variables_list)
        return StatusResponse(**result)
        
    except VariablesServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error uploading variables: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload variables")


@router.delete("/duplicates", response_model=StatusResponse)
def remove_duplicates():
    """Remove duplicate variables (case-insensitive by deviceName)."""
    try:
        result = variables_service.remove_duplicates()
        return StatusResponse(**result)
        
    except VariablesServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error removing duplicates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to remove duplicates")
