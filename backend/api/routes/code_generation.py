"""
Code Generation Routes

API endpoints for code generation functionality.
"""

import logging
from fastapi import APIRouter, HTTPException

from ...models import NarrativeRequest, GenerateResponse
from ...services import generate_code, CodeGenerationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["Code Generation"])


@router.post("-code", response_model=GenerateResponse)
def generate_code_endpoint(body: NarrativeRequest):
    """
    Generate IEC 61131-3 Structured Text code from natural language.
    
    The process involves:
    1. AI generates intermediate JSON representation
    2. Validator checks the JSON for errors
    3. If errors found, regeneration is attempted
    4. Generator converts valid JSON to Structured Text
    """
    try:
        code = generate_code(body.narrative)
        logger.info("Code generation successful")
        return GenerateResponse(status="ok", code=code)
        
    except CodeGenerationError as e:
        if e.is_validation_error:
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error in code generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
